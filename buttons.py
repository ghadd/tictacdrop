from telebot.types import InlineKeyboardButton
from telebot.types import InlineKeyboardMarkup


def get_button(text, *callback_postfixes):
    return InlineKeyboardButton(
        text,
        callback_data="-".join([
            *callback_postfixes]
        )
    )


def get_play_markup():
    markup = InlineKeyboardMarkup()
    markup.row(get_button('Play with AI.', 'ai'))
    markup.row(get_button('Play with other person.', 'person'))

    return markup


SIGNATURES = ['⠀', '❌', '⭕', '💣', '💩']


def get_field_markup(field):
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
