from peewee import *

from models import states
from models.base import BaseModel
from models.user import User


class Game(BaseModel):
    user1 = ForeignKeyField(User)
    user2 = ForeignKeyField(User, null=True)
    message1 = IntegerField(default=-1)
    message2 = IntegerField(default=-1)

    move = IntegerField(default=1)  # 1 - x, 2 - o
    state = IntegerField(default=states.NOT_CREATED_GAME)
    type = IntegerField()

    field = CharField()  # json representation of 4x4 matrix of integers
