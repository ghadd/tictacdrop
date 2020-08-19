import json
import re

import jsonpickle
import telebot

import buttons
import config
import utils
from models import states
from models.game import Game
from models.user import User
import logger

# predefining bot client
bot = telebot.TeleBot(config.TOKEN)

# creating needed database tables
User.create_table()
Game.create_table()

# introducing a logger
logger = logger.get_logger(__name__)


@bot.message_handler(commands=['start'])
def start(msg: telebot.types.Message):
    """
    Handles /start queries coming with msg - registers the user
    :param msg: incoming message update
    """
    logger.info(f'New /start command from id: {msg.from_user.id}.')

    bot.send_message(
        msg.from_user.id,
        'Hello, welcome to TicTacDrop!',
        reply_markup=buttons.get_play_markup()
    )

    utils.save_user(msg.from_user)


@bot.message_handler(commands=['game'])
def game_f(msg: telebot.types.Message):
    """
    Handles /game queries coming with msg - sends game markup if user is not in game
    :param msg: incoming message update
    :return: Terminates with corresponding response when user is not registered
    """
    user = utils.get_user_or_none(msg.from_user)
    if not user:
        bot.send_message(
            msg.from_user.id,
            'Probably, you are not registered. Press /start.'
        )
        return

    if not utils.get_users_game(user):
        user.state = states.USER_IN_MENU
        utils.update_user(user)
    else:
        bot.send_message(
            msg.from_user.id,
            "Hey, you are in active game."
        )

    logger.info(f'New /game command from id: {msg.from_user.id}.')

    bot.send_message(
        msg.from_user.id,
        'Wanna play?',
        reply_markup=buttons.get_play_markup()
    )


@bot.message_handler(commands=['stats'], func=lambda msg: utils.exists_user(msg.from_user))
def stats(msg: telebot.types.Message):
    """
    Handles /stats queries coming with msg - replies with corresponding statistics
    :param msg: incoming message update
    :return: Terminates with corresponding response when user is not registered
    """
    logger.info(f'New /stats command from id: {msg.from_user.id}.')

    user = utils.get_user_or_none(msg.from_user)
    if not user:
        bot.send_message(
            msg.from_user.id,
            'Probably, you are not registered. Press /start.'
        )
        return

    bot.send_message(
        msg.from_user.id,
        'Wins: {wins}\nLosses: {losses}\nDraws: {draws}\nWin rate: {wr:.2f}%'.format(
            wins=user.wins,
            losses=user.losses,
            draws=user.draws,
            wr=user.wins * 100 / (user.wins + user.losses + user.draws) if user.wins + user.losses > 0 else 0
        ) if user else 'No stats yet.'
    )


@bot.message_handler(commands=['leave'])
def leave(msg: telebot.types.Message):
    """
    Handles /leave query coming with msg - leaves the game (counting as lose) and changes your
    signatures to poop emoji
    :param msg: incoming message update
    :return: Terminates with corresponding response when user is not registered
    or is not in game
    """
    if utils.in_menu(msg.from_user):
        bot.reply_to(
            msg,
            'This command outside of game is useless.'
        )
        return

    game, user, opponent = utils.get_game_user_opponent(msg.from_user)
    if not game or not user:
        # todo log something
        return

    user.state = states.USER_IN_MENU
    user.losses += 1
    utils.update_user(user)
    bot.send_message(
        user.user_id,
        'You surrendered.'
    )

    if opponent:
        opponent.state = states.USER_IN_MENU
        opponent.wins += 1
        utils.update_user(opponent)
        bot.send_message(
            opponent.user_id,
            'Your opponent surrendered'
        )

    field = json.loads(game.field)
    sig = 1 if user == game.user1 else 2

    # changes users emojis to poop
    for i in range(len(field)):
        for j in range(len(field[i])):
            if field[i][j] == sig:
                field[i][j] = 4

    if opponent:
        utils.send_updated_field(bot, field, game, opponent)
    Game.delete_by_id(game.id)


@bot.message_handler(commands=['get_users'], func=lambda msg: msg.from_user.id in config.DEV_ID)
def get_users(msg: telebot.types.Message):
    """
    Handles /get_users query - sends back a message with all users and their states
    works for DEV_ID only
    :param msg: incoming message update
    """
    users = User.select()
    m = ''
    for user in users:
        menu_caption = "In PVP game" if user.state == states.USER_IN_PVP_GAME else "In AI game" if user.state == states.USER_IN_AI_GAME else "In menu"
        m += f'[{user.first_name}](tg://user?id={user.user_id}) - {menu_caption}\n'

    bot.send_message(
        msg.from_user.id,
        m,
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['get_games'], func=lambda msg: msg.from_user.id in config.DEV_ID)
def get_games(msg: telebot.types.Message):
    """
    Handles /get_games query - sends back a message with all games
    works for DEV_ID only
    :param msg: incoming message update
    """
    games = Game.select()
    m = ''
    for game in games:
        m += f'{game.id}: {jsonpickle.encode(game)}\n'

    bot.send_message(
        msg.from_user.id,
        m
    )


@bot.message_handler(commands=['kick_user'], func=lambda msg: msg.from_user.id in config.DEV_ID)
def kick_user(msg: telebot.types.Message):
    """
    Handles /kick user {user_id} queries. EMERGENCY USE ONLY.
    works for DEV_ID only
    :param msg: incoming message update
    """
    user_id = int(msg.text.split()[1])
    if User.delete().where(User.user_id == user_id).execute():
        bot.send_message(
            msg.from_user.id,
            'OK.'
        )
    else:
        bot.send_message(
            msg.from_user.id,
            'Cannot fo that.'
        )


@bot.message_handler(func=lambda msg: utils.in_pvp_game(msg.from_user))
def proceed_chatting_message(msg: telebot.types.Message):
    """
    Handles any message coming from players in game. Simulates in-game chat.
    :param msg: any msg coming with update
    """
    _, user, receiver = utils.get_game_user_opponent(msg.from_user)
    bot.send_message(
        receiver.user_id,
        f'**{user.first_name}:** __{msg.text}__',
        parse_mode='Markdown',
    )


@bot.message_handler()
def unknown(msg: telebot.types.Message):
    """
    Handles all messages that could not be handled with previous handlers.
    :param msg: incoming message update
    """
    if not utils.exists_user(msg.from_user):
        bot.send_message(
            msg.from_user.id,
            'Press /start to register.'
        )
    else:
        bot.reply_to(
            msg,
            'Unknown command.'
        )


@bot.callback_query_handler(func=lambda cb: utils.in_menu(cb.from_user) and not re.match("[0-9]-[0-9]", cb.data))
def proceed_menu_button_click(cb: telebot.types.CallbackQuery):
    """
    Handles any callback that doesn't match regex of field button click
    coming from users with IN_MENU state
    :param cb: incoming callback update
    """
    logger.info(f'Got callback {cb.data} from id: {cb.from_user.id}.')

    message = bot.send_message(
        cb.from_user.id,
        'Starting the game.'
    )
    user = utils.get_user_or_none(cb.from_user)
    if user:
        utils.update_dissolving_messages(user, 'starting_the_game', message)

    if cb.data == 'ai':
        # TODO inline keyboard for selecting AI difficulty level
        logger.info(f'Starting AI game for id: {cb.from_user.id}.')
        utils.start_new_game(bot, cb.from_user, 'ai')

    elif cb.data == 'person':
        logger.info(f'Starting PVP game for id: {cb.from_user.id}.')
        utils.start_new_game(bot, cb.from_user, 'person')

    logger.info(f'Deleting message {cb.message.text} from chat {cb.from_user.id}.')
    bot.delete_message(
        cb.from_user.id,
        cb.message.message_id
    )

# TODO selecting difficulty level for AI-games
# @bot.callback_query_handler(func=lambda cb: utils.in_menu(cb.from_user) and cb.data in ['s', 'm', 'h'])
# def proceed_game_field_click(cb: telebot.types.CallbackQuery):


@bot.callback_query_handler(func=lambda cb: not utils.in_menu(cb.from_user) and re.match("[0-9]-[0-9]", cb.data))
def proceed_game_field_click(cb: telebot.types.CallbackQuery):
    """
    Handles any game field clicks and performs corresponding actions
    :param cb: incoming callback update
    """
    logger.info(f'Got callback {cb.data} from id: {cb.from_user.id}.')
    utils.handle_game_field_click(bot, cb)


# bot polling entry
if __name__ == '__main__':
    bot.polling(none_stop=True)
