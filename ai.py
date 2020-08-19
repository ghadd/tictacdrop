from config import *
from random import shuffle
from copy import deepcopy


def is_column_valid(board, col):
    return board[0][col] == 0


# check the search range for rows and columns
def is_range_valid(row, col):
    return row in range(ROWS) and col in range(COLS)


# return all valid moves (empty columns) from the board
def get_valid_moves(board):
    return [col for col in range(COLS) if is_column_valid(board, col)]


def make_move(board, col, player):
    # deepcopy is used to take a copy of current board and not affecting the original one
    temp_board = deepcopy(board)
    for row in reversed(range(ROWS)):
        if temp_board[row][col] == 0:
            temp_board[row][col] = player
            return temp_board, row, col


def count_sequence(board, player, length):
    """ Given the board state , the current player and the length of Sequence you want to count
        Return the count of Sequences that have the give length
    """

    def vertical_seq(row, col):
        """Return 1 if it found a vertical sequence with the required length 
        """
        count = 0
        for row_index in range(row, ROWS):
            if board[row_index][col] == board[row][col]:
                count += 1
            else:
                break
        return int(count >= length)

    def horizontal_seq(row, col):
        """Return 1 if it found a horizontal sequence with the required length 
        """
        count = 0
        for col_index in range(col, COLS):
            if board[row][col_index] == board[row][col]:
                count += 1
            else:
                break
        return int(count >= length)

    def neg_diagonal_seq(row, col):
        """Return 1 if it found a negative diagonal sequence with the required length 
        """
        count = 0
        col_index = col
        for row_index in reversed(range(row)):
            if col_index > ROWS:
                break
            elif board[row_index][col_index] == board[row][col]:
                count += 1
            else:
                break
            col_index += 1  # increment column when row is incremented
        return int(count >= length)

    def pos_diagonal_seq(row, col):
        """Return 1 if it found a positive diagonal sequence with the required length 
        """
        count = 0
        col_index = col
        for row_index in range(row, ROWS):
            if col_index > ROWS:
                break
            elif board[row_index][col_index] == board[row][col]:
                count += 1
            else:
                break
            col_index += 1  # increment column when row incremented
        return int(count >= length)

    total_count = 0
    # for each piece in the board...
    for row in range(ROWS):
        for col in range(COLS):
            # ...that is of the player we're looking for...
            if board[row][col] == player:
                # check if a vertical streak starts at (row, col)
                total_count += vertical_seq(row, col)
                # check if a horizontal four-in-a-row starts at (row, col)
                total_count += horizontal_seq(row, col)
                # check if a diagonal (both +ve and -ve slopes) four-in-a-row starts at (row, col)
                total_count += (pos_diagonal_seq(row, col) + neg_diagonal_seq(row, col))
    # return the sum of sequences of length 'length'
    return total_count


def utility_value(board, player):
    """
        A utility function to evaluate the state of the board and report it to the calling function,
        utility value is defined as the  score of the player who calles the function - score of opponent player,
        The score of any player is the sum of each sequence found for this player scalled by large factor for
        sequences with higher lengths.
    """
    opponent = AI_PLAYER if player == HUMAN_PLAYER else HUMAN_PLAYER

    player_score = count_sequence(board, player, 4) * 99999 + \
                  count_sequence(board, player, 3) * 999 + \
                  count_sequence(board, player, 2) * 99

    opponent_fours = count_sequence(board, opponent, 4)
    opponent_score = opponent_fours * 99999 + \
                    count_sequence(board, opponent, 3) * 999 + \
                    count_sequence(board, opponent, 2) * 99

    return float('-inf') if opponent_fours > 0 else player_score - opponent_score


def game_is_over(board):
    """Check if there is a winner in the current state of the board
    """
    return count_sequence(board, HUMAN_PLAYER, 4) >= 1 or count_sequence(board, AI_PLAYER, 4) >= 1


def minimax_alpha_beta(board, depth, player):
    # get array of possible moves
    valid_moves = get_valid_moves(board)
    shuffle(valid_moves)
    best_move = valid_moves[0]
    best_score = float("-inf")

    # initial alpha & beta values for alpha-beta pruning
    alpha = float("-inf")
    beta = float("inf")

    opponent = HUMAN_PLAYER if player == AI_PLAYER else AI_PLAYER

    # go through all of those boards
    for move in valid_moves:
        # create new board from move
        temp_board = make_move(board, move, player)[0]
        # call min on that new board
        board_score = minimize_beta(temp_board, depth - 1, alpha, beta, player, opponent)
        if board_score > best_score:
            best_score = board_score
            best_move = move
    return best_move


def minimize_beta(board, depth, a, b, player, opponent):
    valid_moves = []
    for col in range(7):
        # if column col is a legal move...
        if is_column_valid(board, col):
            # make the move in column col for curr_player
            temp = make_move(board, col, player)[2]
            valid_moves.append(temp)

    # check to see if game over
    if depth == 0 or len(valid_moves) == 0 or game_is_over(board):
        return utility_value(board, player)

    valid_moves = get_valid_moves(board)
    beta = b

    # if end of tree evaluate scores
    for move in valid_moves:
        board_score = float("inf")
        # else continue down tree as long as ab conditions met
        if a < beta:
            temp_board = make_move(board, move, opponent)[0]
            board_score = maximize_alpha(temp_board, depth - 1, a, beta, player, opponent)

        beta = min(beta, board_score)

    return beta


def maximize_alpha(board, depth, a, b, player, opponent):
    valid_moves = []
    for col in range(7):
        # if column col is a legal move...
        if is_column_valid(board, col):
            # make the move in column col for curr_player
            temp = make_move(board, col, player)[2]
            valid_moves.append(temp)
    # check to see if game over
    if depth == 0 or len(valid_moves) == 0 or game_is_over(board):
        return utility_value(board, player)

    alpha = a
    # if end of tree, evaluate scores
    for move in valid_moves:
        board_score = float("-inf")
        if alpha < b:
            temp_board = make_move(board, move, player)[0]
            board_score = minimize_beta(temp_board, depth - 1, alpha, b, player, opponent)

        alpha = max(alpha, board_score)
    return alpha
