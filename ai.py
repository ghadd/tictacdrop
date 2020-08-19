from config import *
import math
import random

def is_valid_location(board, col):
    return board[0][col] == 0


def get_valid_locations(board):
    return [col for col in range(COLS) if is_valid_location(board, col)]


def winning_move(board, piece):
    dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for i in range(ROWS):
        for j in range(COLS):
            if board[i][j] == 0:
                continue
            for dr in dirs:
                try:
                    if board[i][j] == board[i + dr[0]][j + dr[1]] == \
                            board[i + 2 * dr[0]][j + 2 * dr[1]] == \
                            board[i + 3 * dr[0]][j + 3 * dr[1]] == piece:
                        return True
                except IndexError:
                    continue


def is_terminal_node(board):
    return winning_move(board, 1) or winning_move(board, 2) or len(get_valid_locations(board)) == 0

def evaluate_window(window, piece):
    score = 0
    opp_piece = 2 if piece == 1 else 1

    if window.count(piece) == 4:
        score += 100
    elif window.count(piece) == 3 and window.count(0) == 1:
        score += 5
    elif window.count(piece) == 2 and window.count(0) == 2:
        score += 2
    if window.count(opp_piece) == 3 and window.count(0) == 1:
        score -= 100

    print(score)
    return score


def score_position(board, piece):
    score = 0

    ## Score center column
    center_array = [board[i][COLS // 2] for i in range(ROWS)]
    score += center_array.count(piece) * 3

    ## Score Horizontal
    for r in range(ROWS):
        row_array = [board[r][i] for i in range(COLS)]
        for c in range(COLS - 3):
            window = row_array[c:c + 4]
            score += evaluate_window(window, piece)

    ## Score Vertical
    for c in range(COLS):
        col_array = [board[i][c] for i in range(ROWS)]
        for r in range(ROWS - 3):
            window = col_array[r:r + 4]
            score += evaluate_window(window, piece)

    ## Score posiive sloped diagonal
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += evaluate_window(window, piece)

    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + 3 - i][c + i] for i in range(4)]
            score += evaluate_window(window, piece)

    return score


def get_next_open_row(board, col):
    for r in reversed(range(ROWS)):
        if board[r][col] == 0:
            return r


def minimax(board, depth, alpha, beta, maximizingPlayer):
    valid_locations = get_valid_locations(board)
    is_terminal = is_terminal_node(board)
    if depth == 0 or is_terminal:
        if is_terminal:
            if winning_move(board, 2):
                return (None, 100000000000000)
            elif winning_move(board, 1):
                return (None, -10000000000000)
            else:  # Game is over, no more valid moves
                return (None, 0)
        else:  # Depth is zero
            return (None, score_position(board, 2))
    if maximizingPlayer:
        value = -math.inf
        column = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            import copy
            b_copy = copy.deepcopy(board)
            b_copy[row][col] = 2
            new_score = minimax(b_copy, depth - 1, alpha, beta, False)[1]
            if new_score > value:
                value = new_score
                column = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return column, value

    else:  # Minimizing player
        value = math.inf
        column = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            import copy
            b_copy = copy.deepcopy(board)
            b_copy[row][col] = 2
            new_score = minimax(b_copy, depth - 1, alpha, beta, True)[1]
            if new_score < value:
                value = new_score
                column = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return column, value
