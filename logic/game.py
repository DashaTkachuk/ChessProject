from typing import Optional

from logic.ai import ChessAI
from logic.board import Board
from logic.types import Player, Result


class ChessGame:
    def __init__(self, board=None, ai=False):
        self.board = Board.initial() if board is None else board
        self.current_player = Player.white
        self.ai = ChessAI(self, Player.black) if ai else None

    def move_piece(self, start_pos, end_pos) -> Optional[Result]:
        piece = self.board[start_pos]
        if piece is None:
            raise ValueError("No piece at start position")
        if piece.player != self.current_player:
            raise ValueError("It's not your turn")

        moves = piece.possible_moves(start_pos[0], start_pos[1], self.board)
        for move in moves:
            if move.destination == end_pos:
                break
        else:
            raise ValueError("Invalid move")

        move.execute(self.board)

        end_of_the_game = self.board.check_winner()
        if end_of_the_game:
            return end_of_the_game

        self.current_player = self.current_player.opponent
        if self.ai:
            best_move = self.ai.get_best_move(2)
            best_move.execute(self.board)
            end_of_the_game = self.board.check_winner()
            if end_of_the_game:
                return end_of_the_game
            self.current_player = self.current_player.opponent

    def print_board(self):
        for row in self.board.field:
            print(" ".join([f'{piece:terminal}' if piece else "." for piece in row]))

