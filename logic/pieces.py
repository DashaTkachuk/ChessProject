from abc import ABC
from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterable, ClassVar

from logic.moves import Move, MoveCastling, MoveWithPromotion
from logic.types import Player

if TYPE_CHECKING:
    from logic.board import Board


@dataclass(unsafe_hash=True)
class Piece(ABC):
    player: Player = field()
    is_moved: bool = field(default=False)

    def possible_moves(self, x: int, y: int, board: 'Board') -> Iterable[Move]:
        for move in self._possible_moves(x, y, board):
            new_board = deepcopy(board)
            move = deepcopy(move)
            move.execute(new_board)
            if not new_board.is_in_check(self.player):
                yield move

    def _possible_moves(self, x: int, y: int, board: 'Board') -> Iterable[Move]:
        raise NotImplementedError

    def has_possible_move(self, x: int, y: int, board: 'Board') -> bool:
        return any(self.possible_moves(x, y, board))

    def is_check(self, x: int, y: int, board: 'Board') -> bool:
        for move in self._possible_moves(x, y, board):
            if (
                not board[move.destination] is None
                and isinstance(board[move.destination], King)
                and board[move.destination].player != self.player
            ):
                return True
        return False

    def __format__(self, format_spec):
        if format_spec == "terminal":
            return self.__class__.__name__[0].upper()
        else:
            return super().__format__(format_spec)


@dataclass(unsafe_hash=True)
class Pawn(Piece):

    def _possible_moves(self, x: int, y: int, board: 'Board') -> Iterable[Move]:
        direction = self.player.value.direction
        y1 = y + direction
        if (
            board.is_inside((x, y + direction))
            and board[x, y1] is None
        ):
            if y + direction != self.player.value.promotion_row:
                yield Move(self, (x, y), (x, y + direction))
            else:
                yield MoveWithPromotion(self, (x, y), (x, y + direction), promoted_to=Queen(self.player))
            y2 = y + 2 * direction
            if (
                not self.is_moved
                and y == self.player.value.pawn_start_row
                and board[x, y2] is None
            ):
                yield Move(self, (x, y), (x, y + 2 * direction))
        for dx in (-1, 1):
            x1 = x + dx
            y3 = y + direction
            if (
                board.is_inside((x + dx, y + direction))
                and not board[x1, y3] is None
                and board[x + dx, y + direction].player != self.player
            ):
                if y + direction != self.player.value.promotion_row:
                    yield Move(self, (x, y), (x + dx, y + direction))
                else:
                    yield MoveWithPromotion(self, (x, y), (x + dx, y + direction), promoted_to=Queen(self.player))


@dataclass(unsafe_hash=True)
class PieceWithDiscreteMoves(Piece):
    _vectors: ClassVar[list[tuple[int, int]]]

    def _possible_moves(self, x: int, y: int, board: 'Board') -> Iterable[Move]:
        for dx, dy in self._vectors:
            yield from self._possible_moves_in_direction(x, y, dx, dy, board)

    def _possible_moves_in_direction(self, x: int, y: int, dx: int, dy: int, board: 'Board') -> Iterable[Move]:
        x, y = x + dx, y + dy
        if board.is_inside((x, y)):
            cell = board[x, y]
            if cell is None or cell.player != self.player:
                yield Move(self, (x - dx, y - dy), (x, y))


@dataclass(unsafe_hash=True)
class Knight(PieceWithDiscreteMoves):
    _vectors = ((2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2))


@dataclass(unsafe_hash=True)
class King(PieceWithDiscreteMoves):
    _vectors = ((1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1))

    def _possible_moves(self, x: int, y: int, board: 'Board') -> Iterable[Move]:
        yield from super()._possible_moves(x, y, board)
        fig_to_the_left = board[0, y]
        if (
            not self.is_moved
            and isinstance(fig_to_the_left, Rook)
            and fig_to_the_left.player == self.player
            and all(board[xx, y] is None for xx in range(1, x))
        ):
            yield MoveCastling(
                piece=self,
                start_position=(x, y),
                destination=(x - 2, y),
                rock=fig_to_the_left,
                rook_start=(0, y),
                rook_destination=(x - 1, y),
            )
        fig_to_the_right = board[7, y]
        if (
            not self.is_moved
            and isinstance(fig_to_the_right, Rook)
            and fig_to_the_right.player == self.player
            and all(board[xx, y] is None for xx in range(x + 1, 7))
        ):
            yield MoveCastling(
                piece=self,
                start_position=(x, y),
                destination=(x + 2, y),
                rock=fig_to_the_right,
                rook_start=(7, y),
                rook_destination=(x + 1, y),
            )


@dataclass(unsafe_hash=True)
class PieceWithStraightMoves(Piece):
    _directions: ClassVar[list[tuple[int, int]]]

    def _possible_moves(self, x: int, y: int, board: 'Board') -> Iterable[Move]:
        start_x, start_y = x, y
        start_pos = (x, y)
        for dx, dy in self._directions:
            x, y = start_x + dx, start_y + dy
            destination = (x, y)
            while board.is_inside(destination):
                cell = board[x, y]
                if cell is None:
                    yield Move(piece=self, start_position=start_pos, destination=destination)
                elif cell.player != self.player:
                    yield Move(piece=self, start_position=start_pos, destination=destination)
                    break
                else:
                    break
                x += dx
                y += dy
                destination = (x, y)


@dataclass(unsafe_hash=True)
class Bishop(PieceWithStraightMoves):
    _directions = ((1, 1), (1, -1), (-1, 1), (-1, -1))


@dataclass(unsafe_hash=True)
class Rook(PieceWithStraightMoves):
    _directions = ((1, 0), (-1, 0), (0, 1), (0, -1))


@dataclass(unsafe_hash=True)
class Queen(PieceWithStraightMoves):
    _directions = ((1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1))
