import typing
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from logic.pieces import Piece


@dataclass
class Move:
    piece: 'Piece'
    start_position: tuple[int, int]
    destination: tuple[int, int]

    def execute(self, board):
        board[self.destination] = self.piece
        board[self.start_position] = None
        self.piece.is_moved = True


@dataclass
class MoveWithPromotion(Move):
    promoted_to: 'Piece'

    def execute(self, board):
        super().execute(board)
        board[self.destination] = self.promoted_to


@dataclass
class MoveCastling(Move):
    rock: 'Piece'
    rook_start: tuple[int, int]
    rook_destination: tuple[int, int]

    def execute(self, board):
        super().execute(board)
        board[self.rook_destination] = self.rock
        board[self.rook_start] = None
        self.rock.is_moved = True
