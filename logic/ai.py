from copy import deepcopy
from typing import Iterable, TYPE_CHECKING, Tuple

from logic.board import Board
from logic.moves import Move
from logic.pieces import Queen, Rook, Bishop, Knight, Pawn, King
from logic.types import Player

if TYPE_CHECKING:
    from logic.game import ChessGame


class ChessAI:
    def __init__(self, game: 'ChessGame', player: Player):
        self.game = game
        self.player = player
        self.transposition_table = {}

    def get_best_move(self, depth: int) -> Move:
        best_move = None
        best_score = float("-inf")
        alpha = float("-inf")
        beta = float("inf")

        for move, score in self._iter_possible_moves_in_depth(self.game.board, self.player, depth, alpha, beta):
            if score > best_score:
                best_move = move
                best_score = score
        return best_move

    def _iter_possible_moves_in_depth(
        self, board: Board, player: Player, depth: int, alpha: float, beta: float
    ) -> Iterable[Tuple[Move, int]]:
        if depth == 0:
            return None, self._evaluate_board(board)

        moves = self._order_moves(board, player)

        for move in moves:
            board_copy = deepcopy(board)
            move.execute(board_copy)
            board_key = self._hash_board(board_copy)  # Custom hash function for the board

            if board_key in self.transposition_table:
                score = self.transposition_table[board_key]
            else:
                score = -self._search(board_copy, player.opponent, depth - 1, -beta, -alpha)
                self.transposition_table[board_key] = score

            yield move, score

            alpha = max(alpha, score)
            if alpha >= beta:
                break

    def _search(self, board: Board, player: Player, depth: int, alpha: float, beta: float) -> int:
        if depth == 0:
            return self._evaluate_board(board)

        moves = self._order_moves(board, player)

        for move in moves:
            board_copy = deepcopy(board)
            move.execute(board_copy)
            score = -self._search(board_copy, player.opponent, depth - 1, -beta, -alpha)

            alpha = max(alpha, score)
            if alpha >= beta:
                return alpha

        return alpha

    def _evaluate_board(self, board: Board) -> int:
        piece_values = {
            King: 1000,
            Queen: 9,
            Rook: 5,
            Bishop: 3,
            Knight: 3,
            Pawn: 1
        }
        value = 0
        for (pos, piece) in board.iter_pieces():
            piece_value = piece_values[type(piece)]
            if piece.player == self.player:
                value += piece_value
            else:
                value -= piece_value

        end_of_the_game = self.game.board.check_winner()
        if end_of_the_game:
            if end_of_the_game.winner == self.player:
                return 10000
            else:
                return -10000
        return value

    def _order_moves(self, board: Board, player: Player) -> Iterable[Move]:
        capture_moves = []
        non_capture_moves = []

        for (start_pos, piece) in board.iter_pieces(player=player):
            for move in piece.possible_moves(*start_pos, board):
                if board[*move.destination] is not None:
                    capture_moves.append(move)
                else:
                    non_capture_moves.append(move)

        return capture_moves + non_capture_moves

    def _hash_board(self, board: Board) -> int:
        # Custom hash function for the board
        return hash(str(board))
