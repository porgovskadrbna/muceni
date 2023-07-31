from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from db import Base


class User(Base):
    __tablename__ = "users"

    first_name: Mapped[str]
    last_name: Mapped[str]
    grad_year: Mapped[int]

    email: Mapped[str] = Column(String, primary_key=True)
    password: Mapped[str] = Column(String)

    files: Mapped[list["File"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    votes: Mapped[list["Vote"]] = relationship(
        back_populates="voter", cascade="all, delete-orphan"
    )


class File(Base):
    __tablename__ = "files"

    filename: Mapped[str] = Column(String, primary_key=True)
    deleted: Mapped[bool] = Column(Boolean, default=False)

    grade: Mapped[int]
    subject: Mapped[str]
    name: Mapped[str]

    owner_email: Mapped[str] = Column(String, ForeignKey("users.email"))
    owner: Mapped[User] = relationship(back_populates="files")

    votes: Mapped[list["Vote"]] = relationship(
        back_populates="file", cascade="all, delete-orphan"
    )


class Vote(Base):
    __tablename__ = "votes"

    filename: Mapped[str] = Column(
        String, ForeignKey("files.filename"), primary_key=True
    )
    file: Mapped[list[File]] = relationship(back_populates="votes")

    voter_email: Mapped[str] = Column(
        String, ForeignKey("users.email"), primary_key=True
    )
    voter: Mapped[User] = relationship(back_populates="votes")

    value: Mapped[int] = Column(Integer)


class Registration(Base):
    __tablename__ = "registrations"

    first_name: Mapped[str]
    last_name: Mapped[str]
    grad_year: Mapped[int]

    email: Mapped[str]
    token: Mapped[str] = Column(String, primary_key=True)
