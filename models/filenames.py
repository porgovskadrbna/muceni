from enum import IntEnum

from pydantic import BaseModel
from tortoise import fields
from tortoise.models import Model


class Grade(IntEnum):
    PRIMA = 1
    SEKUNDA = 2
    TERCIE = 3
    KVARTA = 4
    KVINTA = 5
    SEXTA = 6
    SEPTIMA = 7
    OKTÁVA = 8


class Filenames(Model):
    filepath = fields.TextField(pk=True)
    name = fields.TextField()
