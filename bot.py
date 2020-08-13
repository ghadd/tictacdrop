import json

import telebot

import buttons
import config
import utils
from models import states
from models.game import Game
from models.user import User

bot = telebot.TeleBot(config.TOKEN)
User.create_table()
Game.create_table()


@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(
        msg.from_user.id,
        'Hello, welcome to 4TacToe!',
        reply_markup=buttons.get_play_markup()
    )

    utils.save_user(msg.from_user)


@bot.message_handler(commands=['game'], func=lambda msg: utils.in_menu(msg.from_user))
def game_f(msg):
    bot.send_message(
        msg.from_user.id,
        'Wanna play?',
        reply_markup=buttons.get_play_markup()
    )


@bot.message_handler(commands=['stats'])
def stats(msg):
    user = utils.get_user_or_none(msg.from_user.id)
    bot.send_message(
        msg.from_user.id,
        'Wins: {wins}\nLosses: {losses}\nWin rate: {wr:.2f}%'.format(
            wins=user.wins,
            losses=user.losses,
            wr=user.wins * 100 / (user.wins + user.losses) if user.wins + user.losses > 0 else 0
        ) if user else 'No stats yet.',
        reply_markup=buttons.get_play_markup()
    )


@bot.message_handler(func=lambda msg: utils.in_game(msg.from_user) and utils.is_pvp_game(msg.from_user))
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
        parse_mode='Markdown'
    )


@bot.callback_query_handler(func=lambda msg: utils.in_menu(msg.from_user) and msg.data == 'ai' or msg.data == 'person')
def proceed_menu_button_click(cb: telebot.types.CallbackQuery):
    bot.send_message(
        cb.from_user.id,
        'Starting the game.'
    )

    if cb.data == 'ai':
        utils.start_new_game(bot, cb.from_user, 'ai')
    elif cb.data == 'person':
        utils.start_new_game(bot, cb.from_user, 'person')

    bot.delete_message(
        cb.from_user.id,
        cb.message.message_id
    )


@bot.callback_query_handler(func=lambda msg: utils.in_game(msg.from_user))
def proceed_game_field_click(cb):
    try:
        x, y = [int(val) for val in cb.data.split('-')]
    except ValueError as e:
        bot.answer_callback_query(
            cb.id,
            "STOP FUCKING PUSHING RANDOM BUTTONS",
            show_alert=True,
        )
        return

    user = utils.get_user_or_none(cb.from_user.id)
    if not user:
        return
    game = Game.get_or_none(Game.user1 == user) or Game.get_or_none(Game.user2 == user)
    if not game:
        return

    opponent = game.user1 if game.user2 == user else game.user2

    if [game.user1, game.user2][game.move - 1].user_id == cb.from_user.id:
        field = json.loads(game.field)
        if field[x][y] != 0:
            bot.answer_callback_query(
                cb.id,
                'NOPE',
                show_alert=True
            )
            return
        k = config.ROWS - 1

        while field[k][y] != 0:
            k -= 1

        field[k][y] = game.move

        game.field = json.dumps(field)
        game.move = 1 if game.move == 2 else 2
        utils.update_game(game)

        bot.answer_callback_query(
            cb.id,
            "OK."
        )

        has_winner, win_coords, win_dir = utils.has_winner(field)
        if has_winner:
            for i in range(4):
                field[win_coords[0] + win_dir[0] * i][win_coords[1] + win_dir[1] * i] = 3
            Game.delete_by_id(game.id)

            user.wins += 1
            user.state = states.USER_IN_MENU
            utils.update_user(user)

            opponent.losses += 1
            opponent.state = states.USER_IN_MENU
            utils.update_user(opponent)

            bot.send_message(
                user.user_id,
                "Congratulations! You won."
            )
            bot.send_message(
                opponent.user_id,
                "Oh. You lost."
            )

        for i in range(2):
            bot.edit_message_text(
                chat_id=[game.user1, game.user2][i].user_id,
                message_id=[game.message1, game.message2][i],
                text='Your turn' if [game.user1, game.user2][i].id == opponent.id else 'Opponents turn.'
            )
            bot.edit_message_reply_markup(
                [game.user1, game.user2][i].user_id,
                [game.message1, game.message2][i],
                reply_markup=buttons.get_field_markup(field)
            )

    else:
        bot.answer_callback_query(
            cb.id,
            "It's not your turn.",
            show_alert=True,
        )


bot.polling(none_stop=True)
