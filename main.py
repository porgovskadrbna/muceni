from aiofiles import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from tortoise.contrib.fastapi import register_tortoise

import db
from models.filenames import Grade, Filenames

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/files", StaticFiles(directory="files"), name="files")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    files = await get_files(list(range(1, 9)))

    return templates.TemplateResponse(
        "home.jinja",
        {
            "request": request,
            "counts": {k: len(v) for k, v in files.items()},
        },
    )


@app.get("/{grade}", response_class=HTMLResponse)
async def grade_page(grade: int, request: Request):
    return templates.TemplateResponse(
        "grade.jinja",
        {
            "request": request,
            "grade": grade,
            "subjects": dict(
                filter(lambda s: grade in s[1]["grades"], SUBJECTS.items())
            ),
        },
    )


@app.get("/{grade}/{subject}", response_class=HTMLResponse)
async def subject_page(grade: int, subject: str, request: Request):
    files = await get_files_grade(grade)

    return templates.TemplateResponse(
        "subject.jinja",
        {
            "request": request,
            "grade": grade,
            "subject": subject,
            "files": filter(lambda f: f.startswith(subject + "_"), files),
        },
    )


async def get_files(grades: list[int]) -> dict[str, list[str]]:
    files = {}

    for grade in grades:
        files[grade] = []

        for file in await os.scandir(f"files/{grade}"):
            if file.is_file() and not file.name.startswith("."):
                files[grade].append(file.name)

        files[grade].sort()

    return files


async def get_files_grade(grade: int) -> list[str]:
    all_files = await get_files([grade])

    return all_files[grade]


SUBJECTS = {
    # "aj": {
    #     "name": "Angličtina",
    #     "emoji": "🇬🇧",
    #     "grades": list(range(1, 9)),
    # },
    "cj": {
        "name": "Čeština",
        "emoji": "🇨🇿",
        "grades": list(range(1, 9)),
    },
}


register_tortoise(
    app,
    config=db.TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True,
)
