from typing import Tuple, Optional, Iterable, Type, Callable, Union

from logic.pieces import Rook, Knight, Bishop, Queen, King, Pawn, Piece
from logic.types import Player, Result, EndReason


class Board:
    def __init__(self, field=None):
        self.field: list[list[Optional[Piece]]] = field or [[None] * 8 for _ in range(8)]

    def __getitem__(self, pos: Tuple[int, int]):
        return self.field[pos[1]][pos[0]]

    def __setitem__(self, pos: Tuple[int, int], piece: Optional[Piece]):
        self.field[pos[1]][pos[0]] = piece

    @staticmethod
    def initial() -> 'Board':
        board = Board()
        board.add_start_pieces()
        return board

    def add_start_pieces(self):
        self[0, 0] = Rook(Player.black)
        self[1, 0] = Knight(Player.black)
        self[2, 0] = Bishop(Player.black)
        self[3, 0] = Queen(Player.black)
        self[4, 0] = King(Player.black)
        self[5, 0] = Bishop(Player.black)
        self[6, 0] = Knight(Player.black)
        self[7, 0] = Rook(Player.black)

        self[0, 7] = Rook(Player.white)
        self[1, 7] = Knight(Player.white)
        self[2, 7] = Bishop(Player.white)
        self[3, 7] = Queen(Player.white)
        self[4, 7] = King(Player.white)
        self[5, 7] = Bishop(Player.white)
        self[6, 7] = Knight(Player.white)
        self[7, 7] = Rook(Player.white)

        for c in range(8):
            self[c, 1] = Pawn(Player.black)
            self[c, 6] = Pawn(Player.white)

    @staticmethod
    def is_inside(pos: Tuple[int, int]) -> bool:
        return 0 <= pos[0] < 8 and 0 <= pos[1] < 8

    def iter_pieces(
        self,
        piece_types: Union[tuple[Type[Piece]], Type[Piece]] = None,
        player: Player = None,
        predicate: Optional[Callable[[tuple[int, int], Piece], bool]] = None,
    ) -> Iterable[tuple[tuple[int, int], Piece]]:
        iter_ = (
            ((x, y), piece)
            for y, row in enumerate(self.field)
            for x, piece in enumerate(row)
            if piece is not None
        )
        if piece_types is not None:
            if not isinstance(piece_types, tuple):
                piece_types = (piece_types,)
            iter_ = ((pos, piece) for pos, piece in iter_ if isinstance(piece, piece_types))
        if player is not None:
            iter_ = ((pos, piece) for pos, piece in iter_ if piece.player == player)
        if predicate is not None:
            iter_ = ((pos, piece) for pos, piece in iter_ if predicate(pos, piece))
        return iter_

    def is_in_check(self, player: Player):
        for (x, y), piece in self.iter_pieces(player=player.opponent):
            if piece.is_check(x, y, self):
                return True
        return False

    def is_in_checkmate(self, player: Player):
        if not self.is_in_check(player):
            return False
        for (x, y), piece in self.iter_pieces(player=player):
            if piece.has_possible_move(x, y, self):
                return False
        return True

    def is_in_stalemate(self, player: Player):
        if self.is_in_check(player):
            return False
        for (x, y), piece in self.iter_pieces(player=player):
            if piece.has_possible_move(x, y, self):
                return False
        return True

    def possible_moves(self, x, y):
        return self[x, y].possible_moves(x, y, self)

    def check_winner(self):
        for player in Player:
            if self.is_in_checkmate(player):
                return Result(winner=player.opponent, end_reason=EndReason.checkmate)
            elif self.is_in_stalemate(player):
                return Result(winner=None, end_reason=EndReason.stalemate)

    def __deepcopy__(self, memodict={}):
        board = Board()
        board.field = [
            [piece.__class__(piece.player, piece.is_moved) if piece is not None else None for piece in row]
            for row in self.field
        ]
        return board

    def hash(self) -> int:
        return hash(
            tuple(
                tuple(piece for piece in row)
            )
            for row in self.field
        )
