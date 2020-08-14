import json

import config
import buttons
from models import states
from models.game import Game
from models.user import User
import logger

logger = logger.get_logger(__name__)


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
            User.losses: user.losses,
            User.draws: user.draws
        }
    ).where(
        User.id == user.id
    ).execute()

    return bool(updated)


def exists_user(usr):
    return bool(User.get_or_none(User.user_id == usr.id))


def save_user(usr):
    if not exists_user(usr):
        logger.info(f'Saving user id: {usr.id}.')
        User.insert(
            user_id=usr.id,
            first_name=usr.first_name,
        ).execute()
    else:
        logger.info(f'User id: {usr.id} is in DB.')


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
        logger.warning(f'User id {user.user_id} is already in game.')
        bot.send_message(
            usr.id,
            'You are in game already.'
        )
        return

    logger.info(f'Setting state of id: {user.user_id} to IN_GAME.')
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
            logger.info(f'No games found.')
            new_game(user, states.PVP_GAME)
        else:
            logger.info(f'User id {user.user_id} is looking for game.')
            join_game(bot, user)


def join_game(bot, user):
    game = Game.get_or_none(Game.state == states.MATCHMAKING_GAME)

    if not game:
        logger.info('No matchmaking game found, creating a new one.')
        new_game(user, states.PVP_GAME)
        return

    game.state = states.RUNNING_GAME
    game.user2 = user
    update_game(game)

    logger.info(f'Sending first game message for {game.user1.user_id} and {game.user2.user_id}')
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
    logger.info(f'id {user.user_id} creates new game.')

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
                            field[i + 3 * dr[0]][j + 3 * dr[1]] and \
                            j + 3 * dr[1] > 0 and i + 3 * dr[0] > 0:
                        return True, (i, j), dr
                except IndexError:
                    continue

    draw = True
    for row in field:
        for el in row:
            if el == 0:
                draw = False
    if draw:
        return True, (0, 0), (0, 0)

    return False, None, None


def handle_draw(bot, game, user, opponent):
    field = [[3 for _ in range(config.COLS)] for _ in range(config.ROWS)]

    send_updated_field(bot, field, game, opponent)
    for u in [user, opponent]:
        bot.send_message(
            u.user_id,
            "It's a draw."
        )

    Game.delete_by_id(game.id)

    user.draws += 1
    opponent.draws += 1
    user.state = states.USER_IN_MENU
    opponent.state = states.USER_IN_MENU

    update_user(user)
    update_user(opponent)


def handle_game_field_click(bot, cb, x, y):
    user = get_user_or_none(cb.from_user.id)
    if not user:
        return
    game = Game.get_or_none(Game.user1 == user) or Game.get_or_none(Game.user2 == user)
    if not game:
        return

    if cb.message.message_id != game.message1 and \
            cb.message.message_id != game.message2:
        bot.answer_callback_query(
            cb.id,
            'This board is outdated.',
            show_alert=True
        )
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
        update_game(game)

        bot.answer_callback_query(
            cb.id,
            "OK."
        )

        winner, win_coords, win_dir = has_winner(field)
        if winner:
            if win_dir == (0, 0):
                logger.info(f'Game {game} ended with draw.')
                handle_draw(bot, game, user, opponent)
            else:
                logger.info(f'Game {game} ended with winner {user.user_id}')
                handle_win(bot, field, game, opponent, user, win_coords, win_dir)
        else:
            send_updated_field(bot, field, game, opponent)

    else:
        bot.answer_callback_query(
            cb.id,
            "It's not your turn.",
            show_alert=True,
        )


def handle_win(bot, field, game, opponent, user, win_coords, win_dir):
    for i in range(4):
        field[win_coords[0] + win_dir[0] * i][win_coords[1] + win_dir[1] * i] = 3
    Game.delete_by_id(game.id)
    user.wins += 1
    user.state = states.USER_IN_MENU
    update_user(user)
    opponent.losses += 1
    opponent.state = states.USER_IN_MENU
    update_user(opponent)
    bot.send_message(
        user.user_id,
        "Congratulations! You won."
    )
    bot.send_message(
        opponent.user_id,
        "Oh. You lost."
    )

    send_updated_field(bot, field, game, opponent)


def send_updated_field(bot, field, game, opponent):
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
