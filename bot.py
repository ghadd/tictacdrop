import json
import re
import threading

import telebot

import buttons
import config
import utils
from models import states
from models.game import Game
from models.user import User
import logger

bot = telebot.TeleBot(config.TOKEN)
User.create_table()
Game.create_table()

logger = logger.get_logger(__name__)


@bot.message_handler(commands=['start'])
def start(msg):
    logger.info(f'New /start command from id: {msg.from_user.id}.')

    bot.send_message(
        msg.from_user.id,
        'Hello, welcome to TicTacDrop!',
        reply_markup=buttons.get_play_markup()
    )

    utils.save_user(msg.from_user)


@bot.message_handler(commands=['game'])
def game_f(msg):
    user = utils.get_user_or_none(msg.from_user.id)
    if not user:
        return

    if not (Game.get_or_none(Game.user1 == user) or Game.get_or_none(Game.user2 == user)):
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
def stats(msg):
    logger.info(f'New /stats command from id: {msg.from_user.id}.')

    user = utils.get_user_or_none(msg.from_user.id)
    if not user:
        logger.warning(f'User id: {msg.from_user.id} looking for stats not found.')
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
def leave(msg):
    if not utils.in_pvp_game(msg.from_user):
        bot.reply_to(
            msg,
            'This command outside of game is useless.'
        )
        return

    user = utils.get_user_or_none(msg.from_user.id)
    if not user:
        return
    game = Game.get_or_none(Game.user1 == user) or Game.get_or_none(Game.user2 == user)
    if not game:
        return

    opponent = game.user1 if game.user2 == user else game.user2

    bot.send_message(
        user.user_id,
        'You surrendered.'
    )
    bot.send_message(
        opponent.user_id,
        'Your opponent surrendered'
    )

    user.state = states.USER_IN_MENU
    opponent.state = states.USER_IN_MENU
    user.losses += 1
    opponent.wins += 1

    utils.update_user(user)
    utils.update_user(opponent)

    field = json.loads(game.field)
    sig = 1 if user == game.user1 else 2

    for i in range(len(field)):
        for j in range(len(field[i])):
            if field[i][j] == sig:
                field[i][j] = 4

    utils.send_updated_field(bot, field, game, opponent)
    Game.delete_by_id(game.id)


@bot.message_handler(commands=['get_users'], func=lambda msg: msg.from_user.id == 662834330)
def get_users(msg):
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


@bot.message_handler(commands=['get_games'], func=lambda msg: msg.from_user.id == 662834330)
def get_games(msg):
    games = Game.select()
    m = ''
    for game in games:
        m += f'{game.id}: {game}\n'

    bot.send_message(
        msg.from_user.id,
        m
    )


@bot.message_handler(commands=['kick_user'], func=lambda msg: msg.from_user.id == 662834330)
def kick_user(msg):
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


# in-game chat handler
@bot.message_handler(func=lambda msg: utils.in_pvp_game(msg.from_user) and utils.is_pvp_game(msg.from_user))
def proceed_chatting_message(msg):
    user = utils.get_user_or_none(msg.from_user.id)
    if not user:
        return

    game = Game.get_or_none(Game.user1 == user) or Game.get_or_none(Game.user2 == user)
    if not game:
        return

    receiver = game.user1 if game.user2 == user else game.user2
    bot.send_message(
        receiver.user_id,
        f'**{user.first_name}:** __{msg.text}__',
        parse_mode='Markdown',
    )


@bot.message_handler()
def unknown(msg):
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
    logger.info(f'Got callback {cb.data} from id: {cb.from_user.id}.')

    message = bot.send_message(
        cb.from_user.id,
        'Starting the game.'
    )
    user = utils.get_user_or_none(cb.from_user.id)
    if user:
        utils.update_dissolving_messages(user, 'starting_the_game', message)

    if cb.data == 'ai':
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


@bot.callback_query_handler(func=lambda cb: utils.in_pvp_game(cb.from_user) and re.match("[0-9]-[0-9]", cb.data))
def proceed_game_field_click(cb):
    logger.info(f'Got callback {cb.data} from id: {cb.from_user.id}.')

    x, y = [int(val) for val in cb.data.split('-')]
    logger.info(f'Proceeding click from id: {cb.from_user.id} to set {(x, y)} value.')
    utils.handle_game_field_click(bot, cb, y)


if __name__ == '__main__':
    bot.polling(none_stop=True)

    # uncomment when extra update layer needed
    # threading.Thread(
    #     target=bot.polling,
    #     args=(True,)
    # ).start()
    #
    # threading.Thread(
    #     target=utils.update_thread,
    #     args=(bot,)
    # ).start()
