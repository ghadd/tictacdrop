import json
from typing import List, Optional, Tuple, Any

import jsonpickle
import telebot
from peewee import ModelSelect

import buttons
import config
import logger
from models import states
from models.game import Game
from models.user import User

# introducing a logger
logger = logger.get_logger(__name__)


def update_game(game: Game) -> bool:
    """
    Updates game record in DB
    :param game: game that needs to be updated in DB
    :return: True if any of DB records were modified, else False
    """
    q = (game.update(
        {
            Game.user1: game.user1,
            Game.user2: game.user2,
            Game.message1: game.message1,
            Game.message2: game.message2,
            Game.move: game.move,
            Game.state: game.state,
            Game.type: game.type,
            Game.field: game.field,
        }
    ).where(
        Game.id == game.id
    ))
    updated = q.execute()

    return bool(updated)


def update_user(user: User) -> bool:
    """
    Updates user record in DB
    :param user: user that needs to be updated in DB
    :return: True if any of DB records were modified, else False
    """
    updated = User.update(
        {
            User.state: user.state,
            User.wins: user.wins,
            User.losses: user.losses,
            User.draws: user.draws,
            User.dissolving_messages: user.dissolving_messages
        }
    ).where(
        User.id == user.id
    ).execute()

    return bool(updated)


def exists_user(usr: telebot.types.User) -> bool:
    """
    Checks if user corresponding to usr is in DB
    :param usr: telebot.types.User object representing telegram user
    :return: True if user record is in DB, False otherwise
    """
    return bool(User.get_or_none(User.user_id == usr.id))


def save_user(usr: telebot.types.User) -> bool:
    """
    Saves corresponding User model for telebot.types.User to DB
    :param usr: telebot.types.User object representing telegram user
    :return: True if any of DB records were modified/inserted
    """
    if not exists_user(usr):
        logger.info(f'Saving user id: {usr.id}.')
        User.insert(
            user_id=usr.id,
            first_name=usr.first_name,
        ).execute()
        return True
    else:
        logger.info(f'User id: {usr.id} is in DB.')
        return False


def in_pvp_game(usr: telebot.types.User) -> bool:
    """
    Says whether usr is in PVP game currently
    :param usr: telebot.types.User object representing telegram user
    :return: True if usr is in PVP game, False otherwise
    """
    user = User.get_or_none(User.user_id == usr.id)
    if not user:
        return False

    return user.state == states.USER_IN_PVP_GAME


def in_ai_game(usr: telebot.types.User) -> bool:
    """
    Says whether usr is in AI game currently
    :param usr: telebot.types.User object representing telegram user
    :return: True if usr is in AI game, False otherwise
    """
    user = User.get_or_none(User.user_id == usr.id)
    if not user:
        return False

    return user.state == states.USER_IN_AI_GAME


def in_menu(usr: telebot.types.User) -> bool:
    """
    Says whether usr is in menu currently
    :param usr: telebot.types.User object representing telegram user
    :return: True if usr is in menu, False otherwise
    """
    user = User.get_or_none(User.user_id == usr.id)
    if not user:
        return False

    return user.state == states.USER_IN_MENU


def get_games() -> List[ModelSelect]:
    """
    :return: List of all games running/matchmaking
    """
    return Game.select()


def get_user_or_none(usr: telebot.types.User) -> Optional[User]:
    """
    :param usr: telebot.types.User object representing telegram user
    :return: User object corresponding to given user_id, None if not found
    """
    return User.get_or_none(User.user_id == usr.id)


def get_users_game(user: User) -> Optional[Game]:
    """
    Returns user's game if exists
    :param user: User object, whose game is being retrieved
    :return: user's game (or None)
    """
    return Game.get_or_none(Game.user1 == user) or Game.get_or_none(Game.user2 == user)


def get_game_user_opponent(usr: telebot.types.User) -> Tuple[Optional[Game], Optional[User], Optional[User]]:
    """
    Gets users game, own profile and current opponent profile
    :param usr: telebot.types.User object representing telegram user
    :return: user's game (or None) & user (or None) & opponent (or None)
    """
    user = get_user_or_none(usr)
    if not user:
        return None, None, None
    game = Game.get_or_none(Game.user1 == user) or Game.get_or_none(Game.user2 == user)
    if not game:
        return None, None, None
    opponent = game.user1 if game.user2 == user else game.user2

    return game, user, opponent


def handle_ai_game(bot: telebot.TeleBot, user: User) -> None:
    """
    :param bot:
    :param user:
    """
    # TODO all logic
    bot.send_message(
        user.user_id,
        'In development...'
    )
    # logger.info(f'Setting state of id: {user.user_id} to IN_AI_GAME.')
    # user.state = states.USER_IN_AI_GAME
    # update_user(user)


def handle_pvp_game(bot: telebot.TeleBot, user: User) -> None:
    """
    Handles starting/joining pvp game from user
    :param bot: Bot object that manages all the stuff
    :param user: User object to join pvp game
    """
    logger.info(f'Setting state of id: {user.user_id} to IN_PVP_GAME.')
    user.state = states.USER_IN_PVP_GAME
    update_user(user)
    message = bot.send_message(
        user.user_id,
        'Matchmaking...'
    )

    update_dissolving_messages(user, 'matchmaking', message)
    games = get_games()
    if not games:
        logger.info(f'No games found.')
        new_game(user, states.PVP_GAME)
    else:
        logger.info(f'User id {user.user_id} is looking for game.')
        join_pvp_game(bot, user)


def start_new_game(bot: telebot.TeleBot, usr: telebot.types.User, mode: str) -> None:
    """
    Starts a new game leading with usr
    :param bot: Bot object that manages all the stuff
    :param usr: telebot.types.User object of person, who creates a game
    :param mode: either 'ai' or 'person' string
    :return: None. Terminates when user is already in game
    """
    user = get_user_or_none(usr)

    if user.state == states.USER_IN_PVP_GAME:
        logger.warning(f'User id {user.user_id} is already in game.')
        bot.send_message(
            usr.id,
            'You are in game already.'
        )
        return

    if mode == 'ai':
        handle_ai_game(bot, user)
    elif mode == 'person':
        handle_pvp_game(bot, user)


def new_game(user: User, game_type: int) -> None:
    """
    Creates a new matchmaking game with user and givenn type
    :param user: User object to be a part of game
    :param game_type: either states.PVP_GAME or states.AI_GAME
    """
    logger.info(f'id {user.user_id} creates new game.')

    Game.insert(
        user1=user,
        type=game_type,
        state=states.MATCHMAKING_GAME,
        field=json.dumps([[0 for _ in range(config.COLS)] for _ in range(config.ROWS)])
    ).execute()


# not used now, will be helpful for inline mode
def new_game_from2(bot: telebot.TeleBot, user1: User, user2: User) -> None:
    """
    Instantly creates and runs a running game with user1 and user2
    :param bot: Bot object that manages all the stuff
    :param user1: User that will be added to a game
    :param user2: User that will be added to a game
    """
    logger.info(f'id {user1.user_id} and id {user2.user_id} are creating a new game.')

    game1 = get_users_game(user1)
    game2 = get_users_game(user2)

    if game1:
        Game.delete_by_id(game1.id)
    if game2:
        Game.delete_by_id(game2.id)

    game = Game.create(
        user1=user1,
        user2=user2,
        type=states.PVP_GAME,
        state=states.RUNNING_GAME,
        field=json.dumps([[0 for _ in range(config.COLS)] for _ in range(config.ROWS)])
    )

    send_first_game_message(bot, game)


def join_pvp_game(bot: telebot.TeleBot, user: User) -> None:
    """
    Inserts user to an existing matchmaking game. In case game is already filled, creates  a new one
    :param bot: Bot object that manages all the stuff
    :param user: User object to join pvp game
    :return: Terminates if creating new game scenario triggered
    """
    game = Game.get_or_none(Game.state == states.MATCHMAKING_GAME)

    if not game:
        logger.info('No matchmaking game found, creating a new one.')
        new_game(user, states.PVP_GAME)
        return

    game.state = states.RUNNING_GAME
    game.user2 = user
    update_game(game)

    send_first_game_message(bot, game)


def send_first_game_message(bot: telebot.TeleBot, game: Game) -> None:
    """
    Sends a board and a first move tip to players of given game
    :param bot: Bot object that manages all the stuff
    :param game: Game to begin and send first messages and a board to its players
    """
    logger.info(f'Sending first game message for {game.user1.user_id} and {game.user2.user_id}')
    for user in [game.user1, game.user2]:
        message = bot.send_message(
            user.user_id,
            'Game is starting! Your opponent is [{first_name}](tg://user?id={id}). '.format(
                first_name=game.user2.first_name if user == game.user1 else game.user1.first_name,
                id=game.user2.user_id if user == game.user1 else game.user1.user_id
            ) + 'Your signature is `{}`.'.format(config.SIGNATURES[1 if user == game.user1 else 2]),
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
            message = bot.send_message(
                user.user_id,
                'You are starting.'
            )
            update_dissolving_messages(user, 'first_message', message)
        else:
            message = bot.send_message(
                user.user_id,
                'Wait until opponent makes first turn.'
            )
            update_dissolving_messages(user, 'first_message', message)

        delete_dissolving_messages(bot, user, ['starting_the_game', 'matchmaking'])


def update_dissolving_messages(user: User, key: str, message: telebot.types.Message) -> None:
    """
    Adds a message as a value of users dissolving messages with given key
    :param user: User object whose dissolving messages are being updated
    :param key:
    :param message:
    """
    dissolving_messages = json.loads(user.dissolving_messages)
    # using jsonpickle as json.dumps cannot encode an object
    dissolving_messages[key] = jsonpickle.encode(message)
    user.dissolving_messages = json.dumps(dissolving_messages)

    update_user(user)


def get_dissolving_messages(user: User, keys: List[str]) -> List[telebot.types.Message]:
    """
    Returns a list of messages objects stored in corresponding keys skipping those that don't exist
    :param user: User object to look for dissolving messages of
    :param keys: Keys of messages to return
    :return: list of dissolving  messages at given keys
    """
    messages = json.loads(user.dissolving_messages)
    dissolving_messages = []

    for key in keys:
        try:
            dissolving_messages.append(jsonpickle.decode(messages[key]))
        except KeyError:
            continue

    return dissolving_messages


def filter_dissolving_messages(user: User, keys: List[str]) -> None:
    """
    Deletes from dissolving messages records with given keys & syncs with DB
    :param user: User object to look for dissolving messages of
    :param keys: list of dict keys to delete
    """
    logger.info(f'Filtering messages with keys `{keys}` from id {user.user_id}.')
    messages = json.loads(user.dissolving_messages)
    for key in keys:
        try:
            del messages[key]
        except KeyError:
            continue

    user.dissolving_messages = json.dumps(messages)
    update_user(user)


def delete_dissolving_messages(bot: telebot.TeleBot, user: User, keys: List[str]) -> None:
    """
    Deletes sent messages for user that are marked with given keys on DB
    :param bot: Bot object that manages all the stuff
    :param user: User object to whose chat messages will be altered
    :param keys: list of dict keys (labels of messages)
    """
    logger.info(f'Deleting messages with keys `{keys}` from id {user.user_id}.')
    to_delete = get_dissolving_messages(user, keys)
    for message in to_delete:
        bot.delete_message(
            message.chat.id,
            message.message_id
        )

    filter_dissolving_messages(user, keys)


def has_winner(field: List[List[int]]) -> Tuple[bool, Optional[Tuple[int, int]], Optional[Tuple[int, int]]]:
    """
    Checks game for winning (or tie) positions
    :param field: playing field matrix
    :return: Overall answer & position, from where the winning position starts ((0, 0) when tied) &
    winning direction ((0, 0) when tied)
    """
    # directions in which to check winning positions
    dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]

    for i in range(len(field)):
        for j in range(len(field[i])):
            if field[i][j] == 0:
                continue
            for k in range(len(dirs)):
                dr = dirs[k]
                # simply checking an equality of 4 contiguous elements on field
                try:
                    if field[i][j] == field[i + dr[0]][j + dr[1]] == \
                            field[i + 2 * dr[0]][j + 2 * dr[1]] == \
                            field[i + 3 * dr[0]][j + 3 * dr[1]] and \
                            j + 3 * dr[1] > 0 and i + 3 * dr[0] > 0:
                        return True, (i, j), dr
                # to skip border cases without making some stupidly clever algorithm
                except IndexError:
                    continue

    # checking if any empty cells left after checking winning positions as
    # last move can cause it as well
    draw = True
    for row in field:
        for el in row:
            if not el:
                draw = False
    if draw:
        return True, (0, 0), (0, 0)

    return False, None, None


def flatten(lst: List[List[Any]]) -> List[Any]:
    """
    :param lst: list of lists to be flattened
    :return: flattened lst
    """
    return [item for sublist in lst for item in sublist]


def handle_game_field_click(bot: telebot.TeleBot, cb: telebot.types.CallbackQuery) -> None:
    """
    Proceeds a click on game field
    :param bot: Bot object that manages all the stuff
    :param cb: Callback from clicked inline button
    :return: Terminates when callback comes from outdated field
    """
    x, y = [int(val) for val in cb.data.split('-')]
    logger.info(f'Proceeding click from id: {cb.from_user.id} to set {(x, y)} value.')

    game, user, opponent = get_game_user_opponent(cb.from_user)
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

    if [game.user1, game.user2][game.move - 1].user_id == cb.from_user.id:
        field = json.loads(game.field)

        # to perform with first move only
        if sum(flatten(field)) < 2:
            delete_dissolving_messages(bot, user, ['first_message'])
            delete_dissolving_messages(bot, opponent, ['first_message'])

        if field[0][y] != 0:
            bot.answer_callback_query(
                cb.id,
                'This column is full.',
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
                handle_win(bot, field, game, user, opponent, win_coords, win_dir)
        else:
            send_updated_field(bot, field, game, opponent)

    else:
        bot.answer_callback_query(
            cb.id,
            "It's not your turn.",
            show_alert=True,
        )


def handle_draw(bot: telebot.TeleBot, game: Game, user: User, opponent: User) -> None:
    """
    Fills whole field with bombs and ends the game, updates user and opponent draw count
    :param bot: Bot object that manages all the stuff
    :param game: Game where draw occurred
    :param user: Game' player
    :param opponent: Game' player
    """
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


def handle_win(bot: telebot.TeleBot, field: List[List[int]], game: Game, user: User, opponent: User,
               win_coords: Tuple[int, int], win_dir: Tuple[int, int]) -> None:
    """
    Handles winning position in field of given game
    :param bot: Bot object that manages all the stuff
    :param field: matrix of game state
    :param game: Game object where someone won
    :param user: Game' player
    :param opponent: Game' player
    :param win_coords: (x, y) from where the winning position starts
    :param win_dir: (delta_x, delta_y) of where the winning line goes
    """
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


def send_updated_field(bot: telebot.TeleBot, field: List[List[int]], game: Game, opponent: User) -> None:
    """
    Refreshes the game message with new turn hint and field
    :param bot: Bot object that manages all the stuff
    :param field: matrix of game state
    :param game: Game object, where update is needed
    :param opponent: Symbolizes a player, whose turn is next
    """
    for i in range(2):
        bot.edit_message_text(
            chat_id=[game.user1, game.user2][i].user_id,
            message_id=[game.message1, game.message2][i],
            text='Your turn' if [game.user1, game.user2][i] == opponent else 'Opponents turn.'
        )
        bot.edit_message_reply_markup(
            [game.user1, game.user2][i].user_id,
            [game.message1, game.message2][i],
            reply_markup=buttons.get_field_markup(field)
        )
