import json

import config
import buttons
from models import states
from models.game import Game
from models.user import User


def update_game(game: Game):
    q = (game.update(
        {
            Game.user1: game.user1,
            Game.user2: game.user2,
            Game.message1: game.message1,
            Game.message2: game.message2,
            Game.move: game.move,
            Game.state: game.state,
            Game.type: game.type,
            Game.field: game.field
        }
    ).where(
        Game.id == game.id
    ))
    updated = q.execute()

    return bool(updated)


def update_user(user):
    updated = User.update(
        {
            User.state: user.state,
            User.wins: user.wins,
            User.losses: user.losses
        }
    ).where(
        User.id == user.id
    ).execute()

    return bool(updated)


def exists_user(usr):
    return bool(User.get_or_none(User.user_id == usr.id))


def save_user(usr):
    if not exists_user(usr):
        User.insert(
            user_id=usr.id,
            first_name=usr.first_name,
        ).execute()


def in_game(usr):
    user = User.get_or_none(User.user_id == usr.id)
    if not user:
        return False

    return user.state == states.USER_IN_GAME


def in_menu(usr):
    user = User.get_or_none(User.user_id == usr.id)
    if not user:
        return False

    return user.state == states.USER_IN_MENU


def is_pvp_game(usr):
    user = get_user_or_none(usr.id)
    if not user:
        return False
    game = Game.get_or_none(Game.user1 == user) or Game.get_or_none(Game.user2 == user)

    if not game:
        return False

    return game.type == states.PVP_GAME


def get_games():
    return Game.select()


def get_user_or_none(player_id):
    return User.get_or_none(User.user_id == player_id)


def start_new_game(bot, usr, mode):
    user = get_user_or_none(usr.id)
    if user.state == states.USER_IN_GAME:
        bot.send_message(
            usr.id,
            'You are in game already.'
        )
        return
    user.state = states.USER_IN_GAME
    update_user(user)

    if mode == 'ai':
        bot.send_message(
            usr.id,
            'In development...'
        )
    elif mode == 'person':
        bot.send_message(
            usr.id,
            'Matchmaking...'
        )
        games = get_games()
        if not games:
            new_game(user, states.PVP_GAME)
        else:
            join_game(bot, user)


def join_game(bot, user):
    game = Game.get_or_none(Game.state == states.MATCHMAKING_GAME)

    if not game:
        new_game(user, states.PVP_GAME)
        return

    game.state = states.RUNNING_GAME
    game.user2 = user
    update_game(game)

    for user in [game.user1, game.user2]:
        message = bot.send_message(
            user.user_id,
            'Game is starting! Your opponent is [{first_name}](tg://user?id={id}). '.format(
                first_name=game.user2.first_name if user == game.user1 else game.user1.first_name,
                id=game.user2.user_id if user == game.user1 else game.user1.user_id
            ) + 'Your signature is `{}`.'.format(buttons.SIGNATURES[1 if user == game.user1 else 2]),
            parse_mode='Markdown',
            reply_markup=buttons.get_field_markup(
                json.loads(game.field)
            )
        )
        if user == game.user1:
            game.message1 = message.message_id
        else:
            game.message2 = message.message_id
        update_game(game)

        if user == game.user1:
            bot.send_message(
                user.user_id,
                'You are starting.'
            )
        else:
            bot.send_message(
                user.user_id,
                'Wait until opponent makes first turn.'
            )


def new_game(user, game_type):
    Game.insert(
        user1=user,
        type=game_type,
        state=states.MATCHMAKING_GAME,
        field=json.dumps([[0 for _ in range(config.COLS)] for _ in range(config.ROWS)])
    ).execute()


def has_winner(field):
    dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]

    for i in range(len(field)):
        for j in range(len(field[i])):
            if field[i][j] == 0:
                continue
            for k in range(len(dirs)):
                dr = dirs[k]
                try:
                    if field[i][j] == field[i + dr[0]][j + dr[1]] == \
                        field[i + 2 * dr[0]][j + 2 * dr[1]] == \
                            field[i + 3 * dr[0]][j + 3 * dr[1]]:
                        return True, (i, j), dr
                except IndexError:
                    continue

    return False, None, None


