from typing import List

from telebot.types import InlineKeyboardButton
from telebot.types import InlineKeyboardMarkup

from config import SIGNATURES


def get_button(text: str, *callback_postfixes) -> InlineKeyboardButton:
    """
    Generates an InlineKeyboardButton with given text and callback contents
    :param text: Text of button
    :param callback_postfixes: collection of strings which'll form a dash(`-`) separated callback data
    :return:
    """
    return InlineKeyboardButton(
        text,
        callback_data="-".join([
            *callback_postfixes]
        )
    )

def get_ai_level_markup():
    markup = InlineKeyboardMarkup()
    markup.row(get_button('Simple', 's'))
    markup.row(get_button('Medium', 'm'))
    markup.row(get_button('Hard', 'h'))

    return markup

def get_play_markup():
    markup = InlineKeyboardMarkup()
    markup.row(get_button('Play with AI.', 'ai'))
    markup.row(get_button('Play with other person.', 'person'))

    return markup


def get_field_markup(field: List[List[int]]) -> InlineKeyboardMarkup:
    """
    Generates an inline keyboard for given field
    :param field: matrix of game state
    :return: InlineKeyboardMarkup of field
    """
    buttons_field = [[
        InlineKeyboardButton(
            SIGNATURES[field[i][j]],
            callback_data='-'.join(
                [str(i), str(j)]
            )
        ) for j in range(len(field[i]))
    ] for i in range(len(field))]

    markup = InlineKeyboardMarkup()
    for row in buttons_field:
        markup.row(*row)

    return markup
