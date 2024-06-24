import sys
from enum import Enum
from typing import Type

import pygame
from pygame.locals import *

from logic.board import Board
from logic.game import ChessGame
from logic.pieces import King, Queen, Rook, Bishop, Knight, Pawn, Piece
from logic.types import Player, Result

pygame.init()

TILE_SIZE = 90
BOARD_SIZE = TILE_SIZE * 8
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
OVERLAY_COLOR = (0, 0, 0, 128)  # Semi-transparent black


def load_and_resize_image(path, size):
    image = pygame.image.load(path)
    return pygame.transform.scale(image, size)


assets = {
    'KingB': load_and_resize_image('ui/assets/KingB.png', (TILE_SIZE, TILE_SIZE)),
    'KingW': load_and_resize_image('ui/assets/KingW.png', (TILE_SIZE, TILE_SIZE)),
    'QueenB': load_and_resize_image('ui/assets/QueenB.png', (TILE_SIZE, TILE_SIZE)),
    'QueenW': load_and_resize_image('ui/assets/QueenW.png', (TILE_SIZE, TILE_SIZE)),
    'RookB': load_and_resize_image('ui/assets/RookB.png', (TILE_SIZE, TILE_SIZE)),
    'RookW': load_and_resize_image('ui/assets/RookW.png', (TILE_SIZE, TILE_SIZE)),
    'BishopB': load_and_resize_image('ui/assets/BishopB.png', (TILE_SIZE, TILE_SIZE)),
    'BishopW': load_and_resize_image('ui/assets/BishopW.png', (TILE_SIZE, TILE_SIZE)),
    'KnightB': load_and_resize_image('ui/assets/KnightB.png', (TILE_SIZE, TILE_SIZE)),
    'KnightW': load_and_resize_image('ui/assets/KnightW.png', (TILE_SIZE, TILE_SIZE)),
    'PawnB': load_and_resize_image('ui/assets/PawnB.png', (TILE_SIZE, TILE_SIZE)),
    'PawnW': load_and_resize_image('ui/assets/PawnW.png', (TILE_SIZE, TILE_SIZE)),
}


def draw_board(screen, highlighted_tiles: list[tuple[int, int]] = None):
    colors = [WHITE, BLACK]
    for y in range(8):
        for x in range(8):
            if highlighted_tiles is not None and (x, y) in highlighted_tiles:
                color = GREEN
            else:
                color = colors[(x + y) % 2]
            pygame.draw.rect(screen, color, pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))


def draw_pieces(screen, board: Board):
    piece_map: dict[Type[Piece], tuple] = {
        King: ('KingB', 'KingW'),
        Queen: ('QueenB', 'QueenW'),
        Rook: ('RookB', 'RookW'),
        Bishop: ('BishopB', 'BishopW'),
        Knight: ('KnightB', 'KnightW'),
        Pawn: ('PawnB', 'PawnW'),
    }

    for (x, y), piece in board.iter_pieces():
        piece_type = type(piece)
        key = piece_map[piece_type][0] if piece.player == Player.black else piece_map[piece_type][1]
        screen.blit(assets[key], (x * TILE_SIZE, y * TILE_SIZE))


def draw_winner_overlay(screen, win_result: Result):
    overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
    overlay.fill(OVERLAY_COLOR)
    screen.blit(overlay, (0, 0))

    font = pygame.font.Font(None, 74)
    winner = win_result.winner.name if win_result.winner else "Nobody"
    text = font.render(f"{winner} wins! ({win_result.end_reason.name})", True, WHITE)
    screen.blit(text, (BOARD_SIZE // 2 - text.get_width() // 2, BOARD_SIZE // 2 - text.get_height() // 2))

    tip_font = pygame.font.Font(None, 36)
    tip_text = tip_font.render("Press R to restart", True, WHITE)
    screen.blit(tip_text, (BOARD_SIZE // 2 - tip_text.get_width() // 2, BOARD_SIZE // 2 + text.get_height()))


def draw_manual_arrangement_tip(screen):
    font = pygame.font.Font(None, 36)
    tip_text = font.render("Use keys (K,Q,T,B,N,P) to place pieces, C to change color", True, GREEN)
    screen.blit(tip_text, (10, BOARD_SIZE - 40))


class ChessViewModelState(Enum):
    PIECE_NOT_SELECTED = 1
    PIECE_SELECTED = 2
    PIECE_BEING_PLACED = 3


class ChessViewModel:
    def __init__(self, game: ChessGame):
        self.game = game
        self.selected_piece = None
        self.selected_piece_pos = None
        self.possible_moves = []
        self.state = ChessViewModelState.PIECE_NOT_SELECTED
        self.redraw_required = True
        self.manual_arrangement = False
        self.selected_piece_color = Player.white
        self.winner = None

    @staticmethod
    def mouse_coords_to_tile_coords(x, y):
        return x // TILE_SIZE, y // TILE_SIZE

    def handle_click(self, mouse_pos, button):
        if self.winner is not None:
            return

        tile_pos = self.mouse_coords_to_tile_coords(*mouse_pos)
        if button == 3:  # Right click
            self.remove_piece(tile_pos)
        elif self.manual_arrangement and self.selected_piece:
            self.game.board[tile_pos] = self.selected_piece(self.selected_piece_color)
            self.selected_piece = None
            self.redraw_required = True
        else:
            self._handle_click(mouse_pos)
        print(self.state.name, len(self.possible_moves), tile_pos, self.game.board[tile_pos])

    def _handle_click(self, mouse_pos):
        tile_pos = self.mouse_coords_to_tile_coords(*mouse_pos)
        if self.state == ChessViewModelState.PIECE_NOT_SELECTED:
            piece = self.game.board[tile_pos]
            if piece is None:
                return
            if piece.player != self.game.current_player:
                return
            possible_moves = list(self.game.board.possible_moves(*tile_pos))
            if len(possible_moves) == 0:
                return
            self.selected_piece = piece
            self.selected_piece_pos = tile_pos
            self.state = ChessViewModelState.PIECE_SELECTED
            self.possible_moves = possible_moves
            self.redraw_required = True
        elif self.state == ChessViewModelState.PIECE_SELECTED:
            for move in self.possible_moves:
                if move.destination == tile_pos:
                    self.game.move_piece(self.selected_piece_pos, tile_pos)
                    break
            self.state = ChessViewModelState.PIECE_NOT_SELECTED
            self.selected_piece = None
            self.possible_moves = []
            self.redraw_required = True
            self.selected_piece_pos = None
        self.check_winner()

    def remove_piece(self, tile_pos):
        self.game.board[tile_pos] = None
        self.redraw_required = True

    def start_manual_arrangement(self):
        self.manual_arrangement = True
        self.redraw_required = True

    def place_piece(self, piece_type):
        self.selected_piece = piece_type
        self.state = ChessViewModelState.PIECE_BEING_PLACED
        self.redraw_required = True

    def toggle_piece_color(self):
        self.selected_piece_color = Player.black if self.selected_piece_color == Player.white else Player.white

    def start_game(self):
        self.manual_arrangement = False
        self.redraw_required = True
        self.state = ChessViewModelState.PIECE_NOT_SELECTED
        self.check_winner()

    def check_winner(self):
        winner = self.game.board.check_winner()
        if winner:
            self.winner = winner
            self.redraw_required = True

    def restart_game(self):
        self.__init__(ChessGame(Board()))
        self.redraw_required = True

    def clear_board(self):
        self.game = ChessGame(Board())
        self.selected_piece = None
        self.selected_piece_pos = None
        self.possible_moves = []
        self.state = ChessViewModelState.PIECE_NOT_SELECTED
        self.redraw_required = True


def main():
    screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))
    pygame.display.set_caption('Chess')
    clock = pygame.time.Clock()
    fps = 30

    vm = choice_menu(screen)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                vm.handle_click(event.pos, event.button)
            elif event.type == pygame.KEYDOWN:
                if event.key == K_r:
                    vm = choice_menu(screen)
                elif vm.manual_arrangement:
                    handle_manual_arrangement_key(vm, event.key)
                elif event.key == K_a:
                    vm.clear_board()
                if event.key == K_RETURN and vm.manual_arrangement:
                    vm.start_game()

        mouse_pos = pygame.mouse.get_pos()
        if vm.redraw_required:
            draw_game(screen, vm, mouse_pos)
        elif vm.manual_arrangement and vm.selected_piece:
            draw_game(screen, vm, mouse_pos)
            draw_preview(screen, vm, mouse_pos)

        clock.tick(fps)


def draw_preview(screen, vm: ChessViewModel, mouse_pos):
    if vm.selected_piece:
        piece_type = vm.selected_piece
        color = 'B' if vm.selected_piece_color == Player.black else 'W'
        key = f"{piece_type.__name__}{color}"
        preview_image = assets[key].copy()
        preview_image.set_alpha(128)  # Set transparency
        screen.blit(preview_image, (mouse_pos[0] - TILE_SIZE // 2, mouse_pos[1] - TILE_SIZE // 2))


def choice_menu(screen):
    choice = show_menu(screen)
    if choice == 'automatic_pvp':
        vm = ChessViewModel(ChessGame())
    elif choice == 'automatic_pvc':
        vm = ChessViewModel(ChessGame(ai=True))
    elif choice == 'manual_pvp':
        game = ChessGame(Board())
        vm = ChessViewModel(game)
        vm.start_manual_arrangement()
    elif choice == 'manual_pvc':
        game = ChessGame(Board(), ai=True)
        vm = ChessViewModel(game)
        vm.start_manual_arrangement()
    return vm


def show_menu(screen):
    font = pygame.font.Font(None, 52)
    text = font.render('Chess Setup', True, BLACK)
    auto_pvp_text = font.render('1. Automatic Player vs Player', True, BLACK)
    auto_pvc_text = font.render('2. Automatic Player vs Computer', True, BLACK)
    manual_pvp_text = font.render('3. Manual Player vs Player', True, BLACK)
    manual_pvc_text = font.render('4. Manual Player vs Computer', True, BLACK)

    while True:
        screen.fill(WHITE)
        screen.blit(text, (BOARD_SIZE // 2 - text.get_width() // 2, BOARD_SIZE // 8))
        screen.blit(auto_pvp_text, (BOARD_SIZE // 2 - auto_pvp_text.get_width() // 2, BOARD_SIZE // 4))
        screen.blit(auto_pvc_text, (BOARD_SIZE // 2 - auto_pvc_text.get_width() // 2, BOARD_SIZE // 4 + 80))
        screen.blit(manual_pvp_text, (BOARD_SIZE // 2 - manual_pvp_text.get_width() // 2, BOARD_SIZE // 2))
        screen.blit(manual_pvc_text, (BOARD_SIZE // 2 - manual_pvc_text.get_width() // 2, BOARD_SIZE // 2 + 80))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_1:
                    return 'automatic_pvp'
                elif event.key == K_2:
                    return 'automatic_pvc'
                elif event.key == K_3:
                    return 'manual_pvp'
                elif event.key == K_4:
                    return 'manual_pvc'


def handle_manual_arrangement_key(vm, key):
    piece_types = {
        K_k: King,
        K_q: Queen,
        K_t: Rook,
        K_b: Bishop,
        K_n: Knight,
        K_p: Pawn
    }
    if key in piece_types:
        vm.place_piece(piece_types[key])
    elif key == K_c:
        vm.toggle_piece_color()


def draw_game(screen, vm: ChessViewModel, mouse_pos=None):
    highlighted_tiles = [move.destination for move in vm.possible_moves]
    draw_board(screen, highlighted_tiles)
    draw_pieces(screen, vm.game.board)
    if vm.manual_arrangement and vm.selected_piece and mouse_pos:
        draw_preview(screen, vm, mouse_pos)
    if vm.manual_arrangement:
        draw_manual_arrangement_tip(screen)
    if vm.winner:
        draw_winner_overlay(screen, vm.winner)
    pygame.display.flip()
    vm.redraw_required = False


if __name__ == '__main__':
    main()
