from dataclasses import dataclass
from enum import Enum
from typing import Optional


@dataclass
class PlayerData:
    name: str
    promotion_row: int
    pawn_start_row: int
    direction: int


class Player(Enum):
    white = PlayerData("white", 0, 6, -1)
    black = PlayerData("black", 7, 1, 1)

    @property
    def opponent(self):
        return Player.black if self == Player.white else Player.white


class EndReason(Enum):
    checkmate = "checkmate"
    stalemate = "stalemate"
    insufficient_material = "insufficient_material"


@dataclass
class Result:
    winner: Optional[Player]
    end_reason: EndReason
