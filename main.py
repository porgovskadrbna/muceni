import asyncio
import json
import re
from os import getenv
from typing import Annotated

import aiofiles
import aiohttp
import dotenv
import requests
from aiofiles import os
from fastapi import (
    BackgroundTasks,
    Cookie,
    Depends,
    FastAPI,
    Form,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.hash import bcrypt
from sqlalchemy import delete, select, func
from sqlalchemy.orm import Session

import app.confirmation
import app.token
import app.orm
import db
from config import SUBJECTS
from models import File, Registration, User, Vote

dotenv.load_dotenv()


api = FastAPI()

api.mount("/static", StaticFiles(directory="static"), name="static")
api.mount("/files", StaticFiles(directory="files"), name="files")

templates = Jinja2Templates(directory="templates")

client = aiohttp.ClientSession()


@api.on_event("shutdown")
async def shutdown():
    await client.close()


class RequiresLoginException(Exception):
    pass


async def redirect() -> bool:
    raise RequiresLoginException


@api.exception_handler(RequiresLoginException)
async def exception_handler(_, __) -> Response:
    return RedirectResponse(url="/login", status_code=303)


def verify_session(
    user_token: str = Cookie(default=None),
    user_email: str = Cookie(default=None),
):
    if not user_email or not user_token:
        raise RequiresLoginException()

    if not bcrypt.verify(getenv("COOKIE_SECRET") + user_email, user_token):
        raise RequiresLoginException()


async def fetch_students():
    people = {}

    async with client.get("https://kdotoje.porgazeen.cz/names.csv") as resp:
        csv = await resp.text()

    for line in csv.split("\n"):
        if line.startswith("#") or not line:
            continue

        data = line.split(",")
        grad_year = data[0]
        name = data[1]
        name_parts = name.split(" ")
        first_name = name_parts[0]
        last_name = name_parts[-1]

        try:
            grad_year = int(grad_year)
        except ValueError:
            continue

        if grad_year not in people:
            people[grad_year] = []

        people[grad_year].append(
            {
                "first_name": first_name,
                "last_name": last_name,
                "grad_year": int(grad_year),
            }
        )

    return people


@api.get("/registrace", response_class=HTMLResponse)
async def registration(request: Request):
    return templates.TemplateResponse(
        "registration.jinja",
        {"request": request, "people": await fetch_students()},
    )


@api.post("/registrace")
async def registration_post(
    request: Request,
    tasks: BackgroundTasks,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
):
    student = None

    async with client.get("https://kdotoje.porgazeen.cz/names.csv") as resp:
        csv = await resp.text()

    for line in csv.split("\n"):
        if line.startswith("#") or not line:
            continue

        data = line.split(",")
        grad_year = data[0]
        name = data[1]
        name_parts = name.split(" ")
        first_name_ = name_parts[0]
        last_name_ = name_parts[-1]

        try:
            grad_year = int(grad_year)
        except ValueError:
            continue

        if first_name == first_name_ and last_name == last_name_:
            student = (int(grad_year), first_name, last_name)
            break

    if student is None:
        return RedirectResponse("/registrace", status_code=303)

    token = app.token.token()

    async with db.SessionLocal() as session:
        registration = Registration(
            first_name=student[1],
            last_name=student[2],
            grad_year=student[0],
            email=email,
            token=token,
        )
        session.add(registration)
        await session.commit()

    tasks.add_task(app.confirmation.send_confirmation_email, email, token)

    return templates.TemplateResponse(
        "confirmation.jinja",
        {"request": request},
    )


@api.get("/nejsem-snitch/{token}", response_class=HTMLResponse)
async def confirmed(token: str, request: Request):
    async with db.SessionLocal() as session:
        registration = await session.execute(
            select(Registration).where(Registration.token == token)
        )

    return templates.TemplateResponse(
        "confirmed.jinja",
        {
            "request": request,
            "token": token if registration.first() is not None else None,
        },
    )


@api.post("/je-safe")
async def create_user(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
):
    async with db.SessionLocal() as session:
        res = (
            await session.execute(
                select(Registration).where(Registration.token == token)
            )
        ).first()

        if res is None:
            return RedirectResponse("/")

        registration = res[0]

        await session.delete(registration)
        await session.execute(
            delete(User).where(User.email == registration.email)
        )

        pw = bcrypt.hash(password)

        user = User(
            first_name=registration.first_name,
            last_name=registration.last_name,
            grad_year=registration.grad_year,
            email=registration.email,
            password=pw,
        )

        session.add(user)
        await session.commit()

    return RedirectResponse("/", status_code=303)


@api.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "login.jinja",
        {"request": request, "people": await fetch_students()},
    )


@api.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    people = await fetch_students()

    async with db.SessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.email == email))
        ).first()

    if not user:
        return templates.TemplateResponse(
            "login.jinja",
            {
                "request": request,
                "error": "Uživatel neexistuje",
                "people": people,
            },
        )

    user = user[0]

    if not bcrypt.verify(password, user.password):
        return templates.TemplateResponse(
            "login.jinja",
            {
                "request": request,
                "error": "Špatný heslo, bouráku",
                "people": people,
            },
            status_code=401,
        )

    response = RedirectResponse("/", status_code=303)
    response.set_cookie("user_email", user.email)
    response.set_cookie(
        "user_token", bcrypt.hash(getenv("COOKIE_SECRET") + user.email)
    )
    return response


@api.get(
    "/", response_class=HTMLResponse, dependencies=[Depends(verify_session)]
)
async def home(request: Request):
    async with db.SessionLocal() as session:
        files = await session.execute(
            select(File, func.coalesce(func.sum(Vote.value), 0))
            .where(File.deleted == False)
            .outerjoin(Vote)
            .group_by(File.filename)
            .order_by(func.sum(Vote.value).desc())
        )

        votes = await session.execute(
            select(Vote).where(
                Vote.voter_email == request.cookies["user_email"]
            )
        )

    return templates.TemplateResponse(
        "home.jinja",
        {
            "request": request,
            "subjects": SUBJECTS,
            "votes": {v[0].filename: v[0].value for v in votes.all()},
            "files": json.dumps(
                [
                    {"score": f[1], **app.orm.object_as_dict(f[0])}
                    for f in files.all()
                ]
            ),
        },
    )


@api.get("/upvote/{filename}", dependencies=[Depends(verify_session)])
async def upvote(filename: str, request: Request):
    async with db.SessionLocal() as session:
        session.add(
            Vote(
                filename=filename,
                voter_email=request.cookies["user_email"],
                value=1,
            )
        )

        await session.commit()

    return 1


@api.get("/downvote/{filename}", dependencies=[Depends(verify_session)])
async def downvote(filename: str, request: Request):
    async with db.SessionLocal() as session:
        session.add(
            Vote(
                filename=filename,
                voter_email=request.cookies["user_email"],
                value=-1,
            )
        )

        await session.commit()

    return -1


@api.get("/unvote/{filename}", dependencies=[Depends(verify_session)])
async def unvote(filename: str, request: Request):
    async with db.SessionLocal() as session:
        await session.execute(
            delete(Vote).where(
                Vote.filename == filename,
                Vote.voter_email == request.cookies["user_email"],
            )
        )

        await session.commit()

    return 0


@api.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("user_email")
    response.delete_cookie("user_token")
    return response


@api.get(
    "/upload",
    response_class=HTMLResponse,
    dependencies=[Depends(verify_session)],
)
async def upload(request: Request):
    return templates.TemplateResponse(
        "upload.jinja",
        {"request": request, "subjects": SUBJECTS},
    )


@api.post(
    "/upload",
    response_class=HTMLResponse,
    dependencies=[Depends(verify_session)],
)
async def upload_file(
    request: Request,
    file: UploadFile,
    grade: int = Form(...),
    subject: str = Form(...),
    name: str = Form(...),
):
    error = lambda e: templates.TemplateResponse(
        "upload.jinja",
        {"request": request, "subjects": SUBJECTS, "error": e},
    )

    if subject not in SUBJECTS.keys():
        return error

    subject = {
        "code": subject,
        **SUBJECTS[subject],
    }

    if grade not in subject["grades"]:
        return error("Špatný ročník")

    if re.match(r"^[a-z0-9_]{2,}$", name) is None:
        return error("Špatný název")

    file.file.seek(0, 2)
    file_size = file.file.tell()
    await file.seek(0)

    if file_size > 12 * 1024 * 1024:
        return error("Soubor je moc chungus, sry")

    id = app.token.token()
    extension = file.filename.split(".")[-1]
    filename = f"{id}.{extension}"

    async with aiofiles.open("files/" + filename, "wb") as f:
        await f.write(await file.read())

    async with db.SessionLocal() as session:
        session.add(
            File(
                filename=filename,
                grade=grade,
                name=name,
                subject=subject["code"],
                owner_email=request.cookies["user_email"],
            )
        )
        await session.commit()

    return templates.TemplateResponse("uploaded.jinja", {"request": request})


@api.get(
    "/profile",
    response_class=HTMLResponse,
    dependencies=[Depends(verify_session)],
)
async def profile(request: Request):
    async with db.SessionLocal() as session:
        user = await session.execute(
            select(User).where(User.email == request.cookies["user_email"])
        )

        files = await session.execute(
            select(File).where(
                File.owner_email == request.cookies["user_email"]
            )
        )

        likes = await session.execute(
            select(Vote)
            .join(Vote.file)
            .where(File.owner_email == request.cookies["user_email"])
        )

    [user, files] = [user.first()[0], files.all()]

    return templates.TemplateResponse(
        "profile.jinja",
        {
            "request": request,
            "user": user,
            "files": list(map(lambda f: f[0], files)),
            "likes": len(likes.all()),
        },
    )


@api.get(
    "/profile/delete/{filename}",
    response_class=HTMLResponse,
    dependencies=[Depends(verify_session)],
)
async def delete_file(filename: str, request: Request):
    async with db.SessionLocal() as session:
        await session.execute(
            delete(File)
            .where(File.filename == filename)
            .where(File.owner_email == request.cookies["user_email"])
        )

        await session.commit()

    return RedirectResponse("/profile", status_code=303)
