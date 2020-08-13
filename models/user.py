from peewee import *

from models import states
from models.base import BaseModel


class User(BaseModel):
    first_name = CharField()
    user_id = IntegerField()
    state = IntegerField(default=states.USER_IN_MENU)

    wins = IntegerField(default=0)
    losses = IntegerField(default=0)
