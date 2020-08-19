from config import *
from random import shuffle
from copy import deepcopy

def isColumnValid(Board, Col):
    return Board[0][Col] == 0

#check the search range for rows and columns
def isRangeValid(row, col):
    return row in range(ROWS) and col in range(COLS)

#return all valid moves (empty columns) from the board
def getValidMoves(Board):
    return [col for col in range(COLS) if isColumnValid(Board, col)]


def makeMove(board, col, player):
    #deepcopy is used to take acopy of current board and not affecting the original one
    tempBoard = deepcopy(board)
    for row in reversed(range(ROWS)):
        if tempBoard[row][col] == 0:
            tempBoard[row][col] = player
            return tempBoard, row, col

def isValidMove(board, col):
    for row in range(ROWS):
        if board[row][col] == 0:
            return True
    return False


def countSequence(board, player, length):
    """ Given the board state , the current player and the length of Sequence you want to count
        Return the count of Sequences that have the give length
    """
    def verticalSeq(row, col):
        """Return 1 if it found a vertical sequence with the required length 
        """
        count = 0
        for rowIndex in range(row, ROWS):
            if board[rowIndex][col] == board[row][col]:
                count += 1
            else:
                break
        return int(count >= length)

    def horizontalSeq(row, col):
        """Return 1 if it found a horizontal sequence with the required length 
        """
        count = 0
        for colIndex in range(col, COLS):
            if board[row][colIndex] == board[row][col]:
                count += 1
            else:
                break
        return int(count >= length)

    def negDiagonalSeq(row, col):
        """Return 1 if it found a negative diagonal sequence with the required length 
        """
        count = 0
        colIndex = col
        for rowIndex in range(row, -1, -1):
            if colIndex > ROWS:
                break
            elif board[rowIndex][colIndex] == board[row][col]:
                count += 1
            else:
                break
            colIndex += 1 # increment column when row is incremented
        return int(count >= length)

    def posDiagonalSeq(row, col):
        """Return 1 if it found a positive diagonal sequence with the required length 
        """
        count = 0
        colIndex = col
        for rowIndex in range(row, ROWS):
            if colIndex > ROWS:
                break
            elif board[rowIndex][colIndex] == board[row][col]:
                count += 1
            else:
                break
            colIndex += 1 # increment column when row incremented
        return int(count >= length)

    totalCount = 0
    # for each piece in the board...
    for row in range(ROWS):
        for col in range(COLS):
            # ...that is of the player we're looking for...
            if board[row][col] == player:
                # check if a vertical streak starts at (row, col)
                totalCount += verticalSeq(row, col)
                # check if a horizontal four-in-a-row starts at (row, col)
                totalCount += horizontalSeq(row, col)
                # check if a diagonal (both +ve and -ve slopes) four-in-a-row starts at (row, col)
                totalCount += (posDiagonalSeq(row, col) + negDiagonalSeq(row, col))
    # return the sum of sequences of length 'length'
    return totalCount

def utilityValue(board, player):
    """ A utility function to evaluate the state of the board and report it to the calling function,
        utility value is defined as the  score of the player who calles the function - score of opponent player,
        The score of any player is the sum of each sequence found for this player scalled by large factor for
        sequences with higher lengths.
    """
    opponent = AI_PLAYER if player == HUMAN_PLAYER else HUMAN_PLAYER

    playerScore    = countSequence(board, player, 4) * 99999 + \
                     countSequence(board, player, 3) * 999 + \
                     countSequence(board, player, 2) * 99

    opponentfours = countSequence(board, opponent, 4)
    opponentScore  = opponentfours * 99999 + \
                     countSequence(board, opponent, 3) * 999 + \
                     countSequence(board, opponent, 2) * 99

    return float('-inf') if opponentfours > 0 else playerScore - opponentScore


def gameIsOver(board):
    """Check if there is a winner in the current state of the board
    """
    return countSequence(board, HUMAN_PLAYER, 4) >= 1 or countSequence(board, AI_PLAYER, 4) >= 1


def MiniMaxAlphaBeta(board, depth, player):
    # get array of possible moves
    validMoves = getValidMoves(board)
    shuffle(validMoves)
    bestMove = validMoves[0]
    bestScore = float("-inf")

    # initial alpha & beta values for alpha-beta pruning
    alpha = float("-inf")
    beta = float("inf")

    opponent = HUMAN_PLAYER if player == AI_PLAYER else AI_PLAYER

    # go through all of those boards
    for move in validMoves:
        # create new board from move
        tempBoard = makeMove(board, move, player)[0]
        # call min on that new board
        boardScore = minimizeBeta(tempBoard, depth - 1, alpha, beta, player, opponent)
        if boardScore > bestScore:
            bestScore = boardScore
            bestMove = move
    return bestMove


def minimizeBeta(board, depth, a, b, player, opponent):
    validMoves = []
    for col in range(7):
        # if column col is a legal move...
        if isValidMove(board, col):
            # make the move in column col for curr_player
            temp = makeMove(board, col, player)[2]
            validMoves.append(temp)

    # check to see if game over
    if depth == 0 or len(validMoves) == 0 or gameIsOver(board):
        return utilityValue(board, player)

    validMoves = getValidMoves(board)
    beta = b

    # if end of tree evaluate scores
    for move in validMoves:
        boardScore = float("inf")
        # else continue down tree as long as ab conditions met
        if a < beta:
            tempBoard = makeMove(board, move, opponent)[0]
            boardScore = maximizeAlpha(tempBoard, depth - 1, a, beta, player, opponent)

        beta = min(beta, boardScore)

    return beta


def maximizeAlpha(board, depth, a, b, player, opponent):
    validMoves = []
    for col in range(7):
        # if column col is a legal move...
        if isValidMove(board, col):
            # make the move in column col for curr_player
            temp = makeMove(board, col, player)[2]
            validMoves.append(temp)
    # check to see if game over
    if depth == 0 or len(validMoves) == 0 or gameIsOver(board):
        return utilityValue(board, player)

    alpha = a
    # if end of tree, evaluate scores
    for move in validMoves:
        boardScore = float("-inf")
        if alpha < b:
            tempBoard = makeMove(board, move, player)[0]
            boardScore = minimizeBeta(tempBoard, depth - 1, alpha, b, player, opponent)

        alpha = max(alpha, boardScore)
    return alpha
