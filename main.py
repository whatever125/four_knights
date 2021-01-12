import pygame
import pygame.freetype
import random
import sys
from dataclasses import dataclass, field
from typing import Any

color_water = (115, 170, 220)
color_font = (255, 255, 255)

all_units = [
    {'name': 'Рыцарь',
     'sprite': 'default',
     'hp': 20,
     'cost': 15,
     'speed': 6,
     'attacks': ('1x10', '-')},
    {'name': 'Пехотинец',
     'sprite': 'heavyinfantry',
     'hp': 30,
     'cost': 20,
     'speed': 4,
     'attacks': (r'2x6', '-')},
    {'name': 'Драгун',
     'sprite': 'dragoon',
     'hp': 25,
     'cost': 25,
     'speed': 9,
     'attacks': ('2x4', '1x12')},
    {'name': 'Лучник',
     'sprite': 'bowman',
     'hp': 15,
     'cost': 15,
     'speed': 7,
     'attacks': ('1x4', '2x8')},
    {'name': 'Всадник',
     'sprite': 'horseman',
     'hp': 25,
     'cost': 25,
     'speed': 9,
     'attacks': ('2x8', '-')},
    {'name': 'Копейщик',
     'sprite': 'pikeman',
     'hp': 25,
     'cost': 15,
     'speed': 7,
     'attacks': ('1x18', '1x5')}
]

colors = ['red', 'blue', 'green', 'yellow', 'pink']

offset_directions = [
    [[-1, -1], [0, -1], [+1, 0],
     [0, +1], [-1, +1], [-1, 0]],
    [[0, -1], [+1, -1], [+1, 0],
     [+1, +1], [0, +1], [-1, 0]]
]


def offset_neighbor(row, col, direction):
    parity = row % 2
    dir = offset_directions[parity][direction]
    return row + dir[1], col + dir[0]


def cube_to_offset(x, y, z):
    col = x + (z - (z % 2)) / 2
    row = z
    return col, row


def offset_to_cube(row, col):
    x = col - (row - (row % 2)) / 2
    z = row
    y = -x - z
    return x, y, z


def offset_to_pixel(row, col):
    x = size * 3 ** 0.5 * (col + 0.5 * (row % 2))
    y = size * 3 / 2 * row
    return round(x) + horizontal_indent, round(y) + vertical_indent


class Application:
    def __init__(self):
        self.button_end_turn = None
        self.rent_unit_surface = None
        self.rent_unit_coords = None
        self.unit_info_surface = None
        self.unit_info_coords = None
        self.choose_attack_surface = None
        self.choose_attack_coords = None
        self.attack_info_surface_1 = None
        self.attack_info_coords_1 = None
        self.attack_info_surface_2 = None
        self.attack_info_coords_2 = None
        self.info_surface = None
        self.info_coords = None
        self.winner_surf = None
        self.winner_coords = None
        self.selected_castle = None
        self.unit1 = None
        self.unit2 = None

    def start(self):
        self.main()

    def main(self):
        while len(players) > 1:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.terminate()
                    return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_pos = event.pos
                        if self.button_end_turn.collidepoint(mouse_pos):
                            self.end_turn()
                            self.hide_information()
                        elif self.rent_unit_surface and pygame.Rect(
                                *self.rent_unit_coords, 600, 600).collidepoint(mouse_pos):
                            self.rent_unit(mouse_pos)
                            self.hide_information()
                        elif self.choose_attack_surface and pygame.Rect(
                                *self.choose_attack_coords, 400, 400).collidepoint(mouse_pos):
                            self.attack(event.pos)
                            self.hide_information()
                        else:
                            self.hide_information()
                            board.get_click(event.pos)
                    if event.button == 3:
                        if board.is_players_castle(event.pos):
                            self.selected_castle = board.get_cell(event.pos)
                            board.make_cells_available()
                            self.hide_information()
                            self.show_rent_unit()
                        elif board.is_unit(event.pos):
                            self.hide_information()
                            self.show_unit_info(event.pos)
                        else:
                            board.make_cells_available()
                            self.hide_information()
                    if event.button == 4:
                        self.zoom_in()
                        self.hide_information()
                    if event.button == 5:
                        self.zoom_out()
                        self.hide_information()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
                        self.zoom_to_original_position()
                        self.hide_information()
                    if event.key == pygame.K_RETURN:
                        self.end_turn()
                        self.hide_information()
                if event.type == pygame.WINDOWRESIZED:
                    self.resize()
                if event.type == pygame.WINDOWENTER:
                    camera.mouse_enter()
                if event.type == pygame.WINDOWLEAVE:
                    camera.mouse_leave()
            screen.fill(color_water)
            camera.update()
            board.render()
            sprites.draw(screen)
            self.show_cursor(pygame.mouse.get_pos())
            units.draw(screen)
            self.show_info()
            self.blit_surfaces()
            pygame.display.flip()
            clock.tick(fps)
        self.show_winner()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN or \
                        event.type == pygame.MOUSEBUTTONDOWN:
                    self.terminate()
            screen.blit(self.winner_surf, self.winner_coords)
            pygame.display.flip()
            clock.tick(fps)

    def blit_surfaces(self):
        screen.blit(self.info_surface, self.info_coords)
        if self.rent_unit_surface:
            screen.blit(self.rent_unit_surface, self.rent_unit_coords)
        if self.unit_info_surface:
            screen.blit(self.unit_info_surface, self.unit_info_coords)
        if self.choose_attack_surface:
            screen.blit(self.choose_attack_surface, self.choose_attack_coords)

    def show_info(self):
        display_width, display_height = pygame.display.get_surface().get_size()
        surf_width, surf_height = display_width * 0.15 + 1, display_height
        self.info_surface = pygame.Surface((surf_width, surf_height))
        self.info_surface.fill((0, 0, 0))
        self.info_surface.set_alpha(210)
        self.info_coords = display_width * 0.85, 0

        self.button_end_turn = pygame.Rect(0.1 * surf_width + self.info_coords[0],
                                           0.85 * surf_height,
                                           0.9 * surf_width,
                                           0.1 * surf_height)
        title1_font.render_to(self.info_surface, (int(0.1 * surf_width), int(0.9 * surf_height)),
                              '-Завершить ход-', color_font)

        name = players[turn].name
        money = players[turn].money
        income = players[turn].income + len(players[turn].villages) - len(players[turn].units)
        villages = len(players[turn].villages)
        castles = len(players[turn].castles)
        units = len(players[turn].units)
        title0_font.render_to(self.info_surface, (25, 25),
                              name, pygame.Color(players[turn].color))
        title1_font.render_to(self.info_surface, (25, 100),
                              f'Деньги: {money}', color_font)
        title1_font.render_to(self.info_surface, (25, 150),
                              f'Доход: {income}', color_font)
        title1_font.render_to(self.info_surface, (25, 200),
                              f'Деревень: {villages}', color_font)
        title1_font.render_to(self.info_surface, (25, 250),
                              f'Замков: {castles}', color_font)
        title1_font.render_to(self.info_surface, (25, 300),
                              f'Юнитов: {units}', color_font)
        if self.unit1:
            title0_font.render_to(self.info_surface, (25, 400),
                                  f'{self.unit1.name}: {self.unit1.delta_hp}',
                                  pygame.Color(self.unit1.player.color))
            title0_font.render_to(self.info_surface, (25, 450),
                                  f'{self.unit2.name}: {self.unit2.delta_hp}',
                                  pygame.Color(self.unit2.player.color))

    def show_rent_unit(self):
        self.rent_unit_surface = pygame.Surface((600, 600))
        self.rent_unit_surface.fill((0, 0, 0))
        self.rent_unit_surface.set_alpha(210)
        display_width, display_height = pygame.display.get_surface().get_size()
        self.rent_unit_coords = (display_width - 600) // 2, (display_height - 600) // 2
        for i in range(len(all_units)):
            unit_info = {
                'Имя': all_units[i]['name'],
                'HP': all_units[i]['hp'],
                'Цена': all_units[i]['cost'],
                'Скорость': all_units[i]['speed'],
                'Атака 1': all_units[i]['attacks'][0],
                'Атака 2': all_units[i]['attacks'][1],
            }
            lines = []
            for inf in unit_info:
                line = inf
                line += ': '
                line += str(unit_info[inf])
                lines.append(line)
            for j in range(len(lines)):
                title3_font.render_to(self.rent_unit_surface,
                                      (200 * (i % 3) + 20, 300 * (i // 3) + 20 * j + 160),
                                      lines[j], color_font)
            unit_image = pygame.image.load(f'data/units/{all_units[i]["sprite"]}.png')
            unit_image = pygame.transform.scale(unit_image, (160, 160))
            unit_rect = unit_image.get_rect(topleft=(200 * (i % 3) + 20, 300 * (i // 3) + 10))
            self.rent_unit_surface.blit(unit_image, unit_rect)

    def rent_unit(self, mouse_pos):
        x, y = mouse_pos
        x -= self.rent_unit_coords[0]
        y -= self.rent_unit_coords[1]
        unit_num = x // 200 + 3 * (y // 300)
        unit = all_units[unit_num]
        player = players[turn]
        coords = self.selected_castle
        neighbors = filter(lambda cell: board.board[cell[0]][cell[1]].region != 'water',
                           [offset_neighbor(*coords, i) for i in range(6)])
        for i in neighbors:
            f = False
            for j in board.units:
                if j.coords == i:
                    f = True
            if not f and player.money >= int(unit['cost']):
                unit = Unit(i, board, player, unit)
                player.add_unit(unit)
                board.units.append(unit)
                board.update_units()
                player.money -= int(unit.cost)
                break

    def show_unit_info(self, mouse_pos):
        self.unit_info_surface = pygame.Surface((200, 140))
        self.unit_info_surface.fill((0, 0, 0))
        self.unit_info_surface.set_alpha(210)
        self.unit_info_coords = mouse_pos
        info = board.unit_info(mouse_pos)
        lines = []
        for inf in info:
            line = inf
            line += ': '
            line += str(info[inf])
            lines.append(line)
        for i in range(len(lines)):
            title3_font.render_to(self.unit_info_surface, (10, 20 * i + 10), lines[i], color_font)

    def show_choose_attack(self, unit1, unit2):
        self.unit1 = unit1
        self.unit2 = unit2
        self.choose_attack_surface = pygame.Surface((400, 400))
        self.choose_attack_surface.fill((0, 0, 0))
        self.choose_attack_surface.set_alpha(210)
        display_width, display_height = pygame.display.get_surface().get_size()
        self.choose_attack_coords = (display_width - 400) // 2, (display_height - 400) // 2

        title1_font.render_to(self.choose_attack_surface, (125, 25), 'Атаковать врага', color_font)
        unit1_image = pygame.transform.scale(unit1.image, (100, 100))
        unit1_rect = unit1_image.get_rect(topleft=(50, 50))
        self.choose_attack_surface.blit(unit1_image, unit1_rect)
        unit2_image = pygame.transform.scale(unit2.image, (100, 100))
        unit2_rect = unit2_image.get_rect(topleft=(250, 50))
        self.choose_attack_surface.blit(unit2_image, unit2_rect)
        title2_font.render_to(self.choose_attack_surface, (0, 175),
                              unit1.name.rjust(24, ' '), color_font)
        title2_font.render_to(self.choose_attack_surface, (200, 175),
                              unit2.name.rjust(24, ' '), color_font)
        title2_font.render_to(self.choose_attack_surface, (0, 200),
                              str(unit1.hp).rjust(24, ' '), color_font)
        title2_font.render_to(self.choose_attack_surface, (200, 200),
                              str(unit2.hp).rjust(24, ' '), color_font)
        title2_font.render_to(self.choose_attack_surface, (130, 275),
                              '--- ближняя ---', color_font)
        title2_font.render_to(self.choose_attack_surface, (50, 275),
                              f'{unit1.melee["attacks"]}x{unit1.melee["damage"]}', color_font)
        title2_font.render_to(self.choose_attack_surface, (300, 275),
                              f'{unit2.melee["attacks"]}x{unit2.melee["damage"]}', color_font)
        if not unit1.ranged:
            return
        if not unit2.ranged:
            title2_font.render_to(self.choose_attack_surface, (130, 340),
                                  '--- дальняя ---', color_font)
            title2_font.render_to(self.choose_attack_surface, (50, 340),
                                  f'{unit1.ranged["attacks"]}x{unit1.ranged["damage"]}', color_font)
            title2_font.render_to(self.choose_attack_surface, (300, 340),
                                  f'-', color_font)
            return
        title2_font.render_to(self.choose_attack_surface, (130, 340),
                              '--- дальняя ---', color_font)
        title2_font.render_to(self.choose_attack_surface, (50, 340),
                              f'{unit1.ranged["attacks"]}x{unit1.ranged["damage"]}', color_font)
        title2_font.render_to(self.choose_attack_surface, (300, 340),
                              f'{unit2.ranged["attacks"]}x{unit2.ranged["damage"]}', color_font)

    def attack(self, mouse_pos):
        x, y = mouse_pos
        y -= self.choose_attack_coords[1]
        if 250 <= y < 310:
            self.unit1.melee_attack(self.unit1.melee, self.unit2)
        if 310 <= y:
            self.unit1.ranged_attack(self.unit1.ranged, self.unit2)

    def show_winner(self):
        self.winner_surf = pygame.Surface((400, 100))
        self.winner_surf.fill((0, 0, 0))
        self.winner_surf.set_alpha(210)
        display_width, display_height = pygame.display.get_surface().get_size()
        self.winner_coords = (display_width - 400) // 2, (display_height - 200) // 2
        title0_font.render_to(self.winner_surf, (25, 30),
                              f'Победил игрок {players[0].name}!', color_font)

    def hide_information(self):
        self.unit_info_surface = None
        self.unit_info_coords = None
        self.rent_unit_surface = None
        self.rent_unit_coords = None
        self.choose_attack_surface = None
        self.choose_attack_coords = None
        self.attack_info_surface_1 = None
        self.attack_info_coords_1 = None
        self.attack_info_surface_2 = None
        self.attack_info_coords_2 = None

    @staticmethod
    def show_cursor(mouse_pos):
        cell = board.get_cell(mouse_pos)
        try:
            region = board.cell_region(*cell)
            available = board.is_cell_available(*cell)
        except Exception:
            return
        if region == 'water' or not available:
            return
        pygame.draw.polygon(screen, pygame.Color('gold'), board.get_cell_vertices(*cell), 1)

    @staticmethod
    def zoom_in():
        global size, delta, board_width, board_height
        if round(size * 1.1) <= 50:
            size = round(size * 1.1)
            delta = round(delta * 1.1)
            board_width = round(board_width * 1.1)
            board_height = round(board_height * 1.1)
            camera.dx = round(camera.dx * 1.1 - board_size[0] * 0.05)
            camera.dy = round(camera.dy * 1.1 - board_size[1] * 0.05)
            board.update_cell_size()
            board.update_units()
            board.update_cells()

    @staticmethod
    def zoom_out():
        global size, delta, board_width, board_height
        if round(size / 1.1) >= 10:
            size = round(size / 1.1)
            delta = round(delta / 1.1)
            board_width = round(board_width / 1.1)
            board_height = round(board_height / 1.1)
            camera.dx = round(camera.dx / 1.1 + board_size[0] * 0.045)
            camera.dy = round(camera.dy / 1.1 + board_size[1] * 0.045)
            board.update_cell_size()
            board.update_units()
            board.update_cells()

    @staticmethod
    def zoom_to_original_position():
        global size, delta, board_width, board_height
        camera.dx = 0
        camera.dy = 0
        size = original_size
        delta = original_delta
        board_width = board_size[0]
        board_height = board_size[1]
        board.update_cell_size()
        board.update_units()
        board.update_cells()

    @staticmethod
    def end_turn():
        global turn
        board.make_cells_available()
        for player in players:
            if not player.units and not player.castles:
                del players[turn]
                if turn > 0:
                    turn -= 1
        if turn == len(players) - 1:
            turn = 0
        else:
            turn += 1
        players[turn].money += (
                players[turn].income + len(players[turn].villages) - len(players[turn].units))
        for i in players[turn].units:
            i.new_turn()

    @staticmethod
    def resize():
        global horizontal_indent, vertical_indent
        new_screen_size = pygame.display.get_surface().get_size()
        new_screen_width, new_screen_height = new_screen_size[0] * 0.9, new_screen_size[1]
        horizontal_indent = round((new_screen_width - board_width) / 2)
        vertical_indent = round((new_screen_height - board_height) / 2)
        board.update_units()

    @staticmethod
    def terminate():
        pygame.quit()
        sys.exit()


class Board:
    def __init__(self, width, height, cell_size):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.board = [[Cell(i, j) for j in range(self.width)] for i in range(self.height)]
        self.selected_unit = None
        self.generate_board()
        self.units = []
        for player in players:
            self.units.append(Unit(player.castles[0].coords, self, player, all_units[0]))
        for i in self.units:
            i.new_turn()

    def generate_board(self):
        board_generator = BoardGenerator(self)
        board_generator.generate()

    def get_cell_vertices(self, row, col):
        x = self.cell_size * 3 ** 0.5 * (col + 0.5 * (row % 2))
        y = self.cell_size * 1.5 * row
        return (round(x + 3 ** 0.5 * self.cell_size / 2) + horizontal_indent + camera.dx,
                round(y) + vertical_indent + camera.dy), \
               (round(x + 3 ** 0.5 * self.cell_size) + horizontal_indent + camera.dx,
                round(y + 0.5 * self.cell_size) + vertical_indent + camera.dy), \
               (round(x + 3 ** 0.5 * self.cell_size) + horizontal_indent + camera.dx,
                round(y + 1.5 * self.cell_size) + vertical_indent + camera.dy), \
               (round(x + 3 ** 0.5 * self.cell_size / 2) + horizontal_indent + camera.dx,
                round(y + 2 * self.cell_size) + vertical_indent + camera.dy), \
               (round(x) + horizontal_indent + camera.dx,
                round(y + 1.5 * self.cell_size) + vertical_indent + camera.dy), \
               (round(x) + horizontal_indent + camera.dx,
                round(y + 0.5 * self.cell_size) + vertical_indent + camera.dy)

    def render(self):
        for row in self.board:
            for cell in row:
                cell.update()

    def get_cell(self, mouse_pos):
        x, y = mouse_pos
        x -= horizontal_indent
        x -= camera.dx
        y -= vertical_indent
        y -= camera.dy
        grid_height = self.cell_size * 1.5
        grid_width = self.cell_size * 3 ** 0.5
        half_width = grid_width / 2
        c = 0.5 * self.cell_size
        m = c / half_width
        row = y // grid_height
        row_is_odd = row % 2 == 1

        if row_is_odd:
            column = (x - half_width) // grid_width
        else:
            column = x // grid_width
        rel_y = y - (row * grid_height)

        if row_is_odd:
            rel_x = (x - (column * grid_width)) - half_width
        else:
            rel_x = x - (column * grid_width)
        if rel_y < (-m * rel_x) + c:
            row -= 1
            if not row_is_odd:
                column -= 1
        elif rel_y < (m * rel_x) - c:
            row -= 1
            if row_is_odd:
                column += 1

        return round(row), round(column)

    def get_click(self, mouse_pos):
        cell = self.get_cell(mouse_pos)
        x, y = cell
        if 0 <= x < self.height and 0 <= y < self.width:
            self.on_click(cell)

    def on_click(self, clicked_cell):
        clicked_row, clicked_col = clicked_cell
        player = players[turn]
        just_selected = False
        if self.selected_unit and self.distance(self.selected_unit.coords, clicked_cell) == 0:
            self.selected_unit = None
            self.make_cells_available()
        elif not self.selected_unit or self.distance(self.selected_unit.coords, clicked_cell) > 1:
            self.make_cells_available()
            for unit in self.units:
                if unit.coords == clicked_cell:
                    if unit in player.units:
                        self.selected_unit = unit
                        just_selected = True
                        self.make_cells_unavailable()
                        available_cells = self.cells_available_from(
                            self.board[clicked_row][clicked_col], unit.mp)
                        self.make_cells_available(*available_cells)
                    else:
                        self.selected_unit = None
                        self.make_cells_available()
                    break
        elif self.distance(self.selected_unit.coords, clicked_cell) == 1:
            for unit in self.units:
                if unit.coords == clicked_cell:
                    if unit not in player.units:
                        self.make_cells_available()
                        if self.selected_unit.turn_attack:
                            app.show_choose_attack(self.selected_unit, unit)
                        self.selected_unit = None
                        return
                    else:
                        self.selected_unit = unit
                        just_selected = True
                        self.make_cells_unavailable()
                        available_cells = self.cells_available_from(
                            self.board[clicked_row][clicked_col], unit.mp)
                        self.make_cells_available(*available_cells)
                    break
        if self.board[clicked_row][clicked_col].region == 'water':
            self.selected_unit = None
            self.make_cells_available()
        elif self.selected_unit and self.board[clicked_row][clicked_col] not in \
                self.cells_available_from(
                    self.board[self.selected_unit.coords[0]][self.selected_unit.coords[1]],
                    self.selected_unit.mp):
            self.selected_unit = None
        elif not just_selected and self.selected_unit:
            self.make_cells_available()
            self.selected_unit.mp -= int(board.distance(self.selected_unit.coords, clicked_cell))
            self.selected_unit.move_to(*clicked_cell)
            self.selected_unit = None

    @staticmethod
    def distance(a, b):
        return (abs(a[0] - b[0])
                + abs(a[0] + a[1] - b[0] - b[1])
                + abs(a[1] - b[1])) / 2

    def cells_available_from(self, start, movement):
        visited = set()
        visited.add(start)
        fringes = [[start]]

        for i in range(1, movement + 1):
            fringes.append([])
            for cell in fringes[i - 1]:
                for direction in range(6):
                    try:
                        neighbor_row, neighbor_col = offset_neighbor(cell.row, cell.col, direction)
                        neighbor = self.board[neighbor_row][neighbor_col]
                        if neighbor not in visited and neighbor.region != 'water':
                            visited.add(neighbor)
                            fringes[i].append(neighbor)
                    except IndexError:
                        pass
                    except Exception as e:
                        print(e)

        return visited

    def is_players_castle(self, mouse_pos):
        row, col = self.get_cell(mouse_pos)
        return self.board[row][col].region == 'castle' and \
               self.board[row][col].player == players[turn]

    def update_cell_size(self):
        self.cell_size = size

    def update_cell_region(self, x, y, region):
        self.board[x][y].region = region

    def update_cells(self):
        for row in self.board:
            for cell in row:
                cell.update()

    def make_cells_available(self, *cells):
        global color_water
        if cells:
            for cell in cells:
                cell.available = True
        else:
            for row in self.board:
                for cell in row:
                    cell.available = True
            color_water = (115, 170, 220)

    def make_cells_unavailable(self, *cells):
        global color_water
        if cells:
            for cell in cells:
                cell.available = False
        else:
            for row in self.board:
                for cell in row:
                    cell.available = False
            color_water = (65, 120, 170)

    def move_cells(self, dx, dy):
        for row in self.board:
            for cell in row:
                cell.move_sprite(dx, dy)

    def cell_region(self, row, col):
        assert 0 <= row < self.width
        assert 0 <= col < self.height
        return self.board[row][col].region

    def is_cell_available(self, row, col):
        assert 0 <= row < self.width
        assert 0 <= col < self.height
        return self.board[row][col].available

    def update_units(self):
        for unit in self.units:
            unit.update()

    def move_units(self, dx, dy):
        for unit in self.units:
            unit.move_sprite(dx, dy)

    def delete_unit(self, unit):
        self.units = list(filter(lambda x: x != unit, self.units))

    def is_unit(self, mouse_pos):
        cell = self.get_cell(mouse_pos)
        for unit in self.units:
            if unit.coords == cell:
                return True
        return False

    def unit_info(self, mouse_pos):
        cell = self.get_cell(mouse_pos)
        info = {}
        for unit in self.units:
            if unit.coords == cell:
                info['Имя'] = unit.name
                info['Игрок'] = unit.player.name
                info['HP'] = unit.hp
                info['Скорость'] = unit.speed
                info['Атака 1'] = f'{unit.melee["attacks"]}x{unit.melee["damage"]}'
                if unit.ranged:
                    info['Атака 2'] = f'{unit.ranged["attacks"]}x{unit.ranged["damage"]}'
                else:
                    info['Атака 2'] = '-'
        return info


class BoardGenerator:
    def __init__(self, board):
        self.width = board.width
        self.height = board.height
        self.board = board

        self.number_of_earth_cells = round((self.width * self.height) / 2)
        self.min_region_cells = round(self.number_of_earth_cells * 0.2)
        self.max_region_cells = round(self.number_of_earth_cells * 0.25)
        self.number_of_villages = round((self.width * self.height) / 100)
        self.region_chance = 40

        self.generator = {(i, j): 'water' for i in range(self.height) for j in range(self.width)}

    def generate(self):
        self.generate_board()
        self.generate_forest()
        self.generate_desert()
        self.generate_mountain()
        self.generate_swamp()
        self.generate_villages()
        self.generate_castles()
        self.update_cells()

    def generate_board(self):
        mid_row = self.height // 2 - 1
        mid_col = self.width // 2 - 1
        mid_cell = mid_row, mid_col
        self.generator[mid_cell] = 'plain'
        self.update_neighbours(mid_cell, 100, 'water', 'pre_plain')
        for _ in range(self.number_of_earth_cells):
            neighbours = list(
                filter(lambda cell: self.generator[cell] == 'pre_plain', self.generator))
            neighbour = random.choice(neighbours)
            self.generator[neighbour] = 'plain'
            self.update_neighbours(neighbour, 40, 'water', 'pre_plain')
        self.delete_pre_cells()

    def generate_forest(self):
        available_cells = list(filter(lambda cell: self.generator[cell] == 'plain', self.generator))
        first_cell = random.choice(available_cells)
        self.generator[first_cell] = 'forest'
        self.update_neighbours(first_cell, 100, 'plain', 'pre_forest')
        number_of_forest_cells = random.randint(self.min_region_cells, self.max_region_cells)
        for _ in range(number_of_forest_cells):
            try:
                available_cells = list(
                    filter(lambda cell: self.generator[cell] == 'pre_forest', self.generator))
                forest_cell = random.choice(available_cells)
                self.generator[forest_cell] = 'forest'
                self.update_neighbours(forest_cell, self.region_chance, 'plain', 'pre_forest')
            except Exception:
                pass
        self.delete_pre_cells()

    def generate_desert(self):
        available_cells = list(filter(lambda cell: self.generator[cell] == 'plain', self.generator))
        first_cell = random.choice(available_cells)
        self.generator[first_cell] = 'desert'
        self.update_neighbours(first_cell, 100, 'plain', 'pre_desert')
        number_of_desert_cells = random.randint(self.min_region_cells, self.max_region_cells)
        for _ in range(number_of_desert_cells):
            try:
                available_cells = list(
                    filter(lambda cell: self.generator[cell] == 'pre_desert', self.generator))
                forest_cell = random.choice(available_cells)
                self.generator[forest_cell] = 'desert'
                self.update_neighbours(forest_cell, self.region_chance, 'plain', 'pre_desert')
            except Exception:
                pass
        self.delete_pre_cells()

    def generate_mountain(self):
        available_cells = list(filter(lambda cell: self.generator[cell] == 'plain', self.generator))
        first_cell = random.choice(available_cells)
        self.generator[first_cell] = 'mountains'
        self.update_neighbours(first_cell, 100, 'plain', 'pre_mountain')
        number_of_mountain_cells = random.randint(self.min_region_cells, self.max_region_cells)
        for _ in range(number_of_mountain_cells):
            try:
                available_cells = list(
                    filter(lambda cell: self.generator[cell] == 'pre_mountain', self.generator))
                forest_cell = random.choice(available_cells)
                self.generator[forest_cell] = 'mountains'
                self.update_neighbours(forest_cell, self.region_chance, 'plain', 'pre_mountain')
            except Exception:
                pass
        self.delete_pre_cells()

    def generate_swamp(self):
        available_cells = list(filter(lambda cell: self.generator[cell] == 'plain', self.generator))
        first_cell = random.choice(available_cells)
        self.generator[first_cell] = 'swamp'
        self.update_neighbours(first_cell, 100, 'plain', 'pre_swamp')
        number_of_swamp_cells = random.randint(self.min_region_cells, self.max_region_cells)
        for _ in range(number_of_swamp_cells):
            try:
                available_cells = list(
                    filter(lambda cell: self.generator[cell] == 'pre_swamp', self.generator))
                forest_cell = random.choice(available_cells)
                self.generator[forest_cell] = 'swamp'
                self.update_neighbours(forest_cell, self.region_chance, 'plain', 'pre_swamp')
            except Exception:
                pass
        self.delete_pre_cells()

    def generate_villages(self):
        for _ in range(self.number_of_villages):
            available_cells = list(
                filter(lambda cell: self.generator[cell] != 'water', self.generator))
            village_cell = random.choice(available_cells)
            self.generator[village_cell] = 'village'

    def generate_castles(self):
        for player in players:
            available_cells = list(
                filter(lambda cell: self.generator[cell] != 'water', self.generator))
            castle_cell = random.choice(available_cells)
            self.generator[castle_cell] = 'castle'
            self.update_neighbours(castle_cell, 100, 'water', 'plain')
            self.board.board[castle_cell[0]][castle_cell[1]].player = player
            player.castles.append(self.board.board[castle_cell[0]][castle_cell[1]])

    def delete_pre_cells(self):
        for cell in self.generator:
            if self.generator[cell].startswith('pre'):
                self.generator[cell] = 'plain'

    def update_neighbours(self, cell, chance, from_region, to_region):
        for direction in range(6):
            try:
                x, y = offset_neighbor(*cell, direction)
                if self.generator[(x, y)] == from_region and random.randint(0, 100) <= chance:
                    self.generator[(x, y)] = to_region
            except Exception:
                pass

    def update_cells(self):
        for cell in self.generator:
            try:
                assert 0 <= cell[0] < self.height
                assert 0 <= cell[1] < self.width
                if self.generator[cell].startswith('pre'):
                    self.board.update_cell_region(*cell, 'plain')
                else:
                    self.board.update_cell_region(*cell, self.generator[cell])
                self.board.board[cell[0]][cell[1]].load_sprite()
            except Exception:
                pass


class Player:
    def __init__(self, color, name):
        self.color = color
        self.units = []
        self.villages = []
        self.castles = []
        self.money = 100
        self.name = name
        self.income = 5

    def delete_unit(self, unit):
        self.units = list(filter(lambda x: x != unit, self.units))

    def add_unit(self, unit):
        self.units.append(unit)

    def delete_village(self, village):
        self.villages = list(filter(lambda x: x != village, self.villages))

    def delete_castle(self, castle):
        self.castles = list(filter(lambda x: x != castle, self.castles))


class Cell:
    def __init__(self, row, col, region='plain', player=None):
        self.region = region
        self.col = col
        self.row = row
        self.coords = (row, col)
        self.cube = offset_to_cube(row, col)
        self.x, self.y, self.z = self.cube
        self.num = random.randint(1, 5)
        self.available = True
        self.captured = False
        self.player = None
        self.player_color = None

    def load_sprite(self):
        self.sprite = pygame.sprite.Sprite()
        if self.player:
            self.image_available = pygame.image.load(
                f'data/cells/{self.region}_{self.player.color}.png')
            self.image_unavailable = pygame.image.load(
                f'data/cells/{self.region}_{self.player.color}_unavailable.png')
        else:
            self.image_available = pygame.image.load(
                f'data/cells/{self.region}{self.num}.png')
            self.image_unavailable = pygame.image.load(
                f'data/cells/{self.region}{self.num}_unavailable.png')
        self.sprite.image = pygame.transform.scale(
            self.image_available, (round(size * 3 ** 0.5) + 2, round(size * 2) + 2))
        self.sprite.rect = self.sprite.image.get_rect()
        pixel = offset_to_pixel(*self.coords)
        self.sprite.rect.x = pixel[0]
        self.sprite.rect.y = pixel[1]
        sprites.add(self.sprite)

    def update(self):
        sprites.remove(self.sprite)
        if self.available:
            self.sprite.image = pygame.transform.scale(
                self.image_available, (round(size * 3 ** 0.5) + 2, round(size * 2) + 2))
        else:
            self.sprite.image = pygame.transform.scale(
                self.image_unavailable, (round(size * 3 ** 0.5) + 2, round(size * 2) + 2))
        self.sprite.rect = self.sprite.image.get_rect()
        pixel = offset_to_pixel(*self.coords)
        self.sprite.rect.x = pixel[0] + camera.dx
        self.sprite.rect.y = pixel[1] + camera.dy
        sprites.add(self.sprite)

    def move_sprite(self, dx, dy):
        self.sprite.rect.x += dx
        self.sprite.rect.y += dy


class Unit:
    def __init__(self, coords, board, player, unit_type):
        self.coords = coords
        self.board = board
        self.player = player
        self.player.add_unit(self)

        self.name = unit_type['name']
        self.cost = unit_type['cost']
        self.sprite_name = unit_type['sprite']
        self.max_hp = unit_type['hp']
        self.hp = self.max_hp
        self.delta_hp = 0
        self.speed = unit_type['speed']
        self.mp = 0
        self.turn_attack = True
        self.defence = 0.5
        melee = unit_type['attacks'][0].split('x')
        self.melee = {'type': 'melee', 'attacks': int(melee[0]), 'damage': int(melee[1]), 'mod': 0}
        if unit_type['attacks'][1] == '-':
            self.ranged = None
        else:
            ranged = unit_type['attacks'][1].split('x')
            self.ranged = {'type': 'ranged', 'attacks': int(ranged[0]),
                           'damage': int(ranged[1]), 'mod': 0}

        self.load_sprite()

    def load_sprite(self):
        self.sprite = pygame.sprite.Sprite()
        self.image = pygame.image.load(f'data/units/{self.sprite_name}_{self.player.color}.png')
        self.sprite.image = pygame.transform.scale(
            self.image, (round(size * 3 ** 0.5), round(size * 2)))
        self.sprite.rect = self.sprite.image.get_rect()
        pixel = offset_to_pixel(*self.coords)
        self.sprite.rect.x = pixel[0]
        self.sprite.rect.y = pixel[1]
        units.add(self.sprite)

    def move_to(self, x, y):
        self.coords = (x, y)
        pixel = offset_to_pixel(*self.coords)
        self.sprite.rect.x = pixel[0] + camera.dx
        self.sprite.rect.y = pixel[1] + camera.dy
        if (not self.board.board[x][y].captured) and (self.board.board[x][y].region == 'village'):
            self.board.board[x][y].captured = True
            self.player.villages.append(board.board[x][y])
            self.board.board[x][y].player_color = self.player.color
            self.board.board[x][y].player = self.player
        elif self.board.board[x][y].captured and self.board.board[x][y].region == 'village':
            self.board.board[x][y].player_color = self.player.color
            self.board.board[x][y].player.delete_village(board.board[x][y])
            self.player.villages.append(board.board[x][y])
        elif board.board[x][y].region == 'castle':
            self.board.board[x][y].player_color = self.player.color
            self.board.board[x][y].player.delete_castle(board.board[x][y])
            self.board.board[x][y].player = self.player
            self.player.castles.append(board.board[x][y])
            board.board[x][y].load_sprite()

    def die(self):
        board.delete_unit(self)
        units.remove(self.sprite)
        if self.player:
            self.player.delete_unit(self)

    def melee_attack(self, attack, enemy):
        self.turn_attack = False
        self.mp = 0
        for i in range(attack['attacks']):
            if random.random() + attack['mod'] > enemy.defence:
                enemy.take_damage(attack['damage'])
                if enemy.hp <= 0:
                    enemy.die()
                    return
        if enemy.melee:
            for i in range(enemy.melee['attacks']):
                if random.random() + enemy.melee['mod'] > self.defence:
                    self.take_damage(enemy.melee['damage'])
                    if self.hp <= 0:
                        self.die()
                        return

    def ranged_attack(self, attack, enemy):
        self.turn_attack = False
        self.mp = 0
        for i in range(attack['attacks']):
            if random.random() + attack['mod'] > enemy.defence:
                enemy.take_damage(attack['damage'])
                if enemy.hp <= 0:
                    enemy.die()
                    return
        if enemy.ranged:
            for i in range(enemy.ranged['attacks']):
                if random.random() + enemy.ranged['mod'] > self.defence:
                    self.take_damage(enemy.ranged['damage'])
                    if self.hp <= 0:
                        self.die()
                        return

    def take_damage(self, damage):
        self.delta_hp = -damage
        self.hp -= damage

    def return_information(self):
        if not self.melee:
            melee = '-'
        else:
            melee = f'{self.melee["attacks"]}x{self.melee["damage"]}'
        if not self.ranged:
            ranged = '-'
        else:
            ranged = f'{self.ranged["attacks"]}x{self.ranged["damage"]}'
        return {'name': self.name,
                'sprite': self.sprite_name,
                'hp': self.hp,
                'cost': self.cost,
                'speed': self.speed,
                'attacks': (melee, ranged)}

    def new_turn(self):
        if self.board.board[self.coords[0]][self.coords[1]].region == 'village':
            self.hp += 8
        else:
            self.hp += 2
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        self.mp = self.speed
        self.turn_attack = True

    def update(self):
        units.remove(self.sprite)
        self.sprite.image = pygame.transform.scale(
            self.image, (round(size * 3 ** 0.5), round(size * 2)))
        self.sprite.rect = self.sprite.image.get_rect()
        pixel = offset_to_pixel(*self.coords)
        self.sprite.rect.x = pixel[0] + camera.dx
        self.sprite.rect.y = pixel[1] + camera.dy
        units.add(self.sprite)

    def move_sprite(self, dx, dy):
        self.sprite.rect.x += dx
        self.sprite.rect.y += dy


@dataclass(order=True)
class PrioritizedItem:
    priority: int
    item: Any = field(compare=False)


class Camera:
    def __init__(self):
        self.dx = 0
        self.dy = 0
        self.mouse_is_in_the_app = False

    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    def update(self):
        if self.mouse_is_on_the_left() and self.mouse_is_in_the_app:
            self.move_camera_to_the_right()
            app.hide_information()

        if self.mouse_is_on_the_right() and self.mouse_is_in_the_app:
            self.move_camera_to_the_left()
            app.hide_information()

        if self.mouse_is_at_the_bottom() and self.mouse_is_in_the_app:
            self.move_camera_to_the_top()
            app.hide_information()

        if self.mouse_is_at_the_top() and self.mouse_is_in_the_app:
            self.move_camera_to_the_bottom()
            app.hide_information()

    @staticmethod
    def mouse_is_on_the_left():
        x, y = pygame.mouse.get_pos()
        surface_size = pygame.display.get_surface().get_size()
        return x <= surface_size[0] * 0.05

    @staticmethod
    def mouse_is_on_the_right():
        x, y = pygame.mouse.get_pos()
        surface_size = pygame.display.get_surface().get_size()
        return x >= surface_size[0] * 0.95

    @staticmethod
    def mouse_is_at_the_bottom():
        x, y = pygame.mouse.get_pos()
        surface_size = pygame.display.get_surface().get_size()
        return y <= surface_size[1] * 0.05

    @staticmethod
    def mouse_is_at_the_top():
        x, y = pygame.mouse.get_pos()
        surface_size = pygame.display.get_surface().get_size()
        return y >= surface_size[1] * 0.95

    def move_camera_to_the_right(self):
        self.dx += delta
        board.move_units(delta, 0)
        board.move_cells(delta, 0)

    def move_camera_to_the_left(self):
        self.dx -= delta
        board.move_units(-delta, 0)
        board.move_cells(-delta, 0)

    def move_camera_to_the_top(self):
        self.dy += delta
        board.move_units(0, delta)
        board.move_cells(0, delta)

    def move_camera_to_the_bottom(self):
        self.dy -= delta
        board.move_units(0, -delta)
        board.move_cells(0, -delta)

    def mouse_enter(self):
        self.mouse_is_in_the_app = True

    def mouse_leave(self):
        self.mouse_is_in_the_app = False


if __name__ == '__main__':
    print(r"""
______                 _   __      _       _     _       
|  ___|               | | / /     (_)     | |   | |      
| |_ ___  _   _ _ __  | |/ / _ __  _  __ _| |__ | |_ ___ 
|  _/ _ \| | | | '__| |    \| '_ \| |/ _` | '_ \| __/ __|
| || (_) | |_| | |    | |\  \ | | | | (_| | | | | |_\__ \
\_| \___/ \__,_|_|    \_| \_/_| |_|_|\__, |_| |_|\__|___/
                                      __/ |              
                                     |___/               
""")
    players = []
    turn = 0
    try:
        num_of_players = int(input('Введите количество игроков (2-5): '))
        assert 2 <= num_of_players <= 5
    except Exception:
        print('Введены неверные данный')
        sys.exit()
    for i in range(num_of_players):
        name = input(f'Введите имя {i + 1} игрока: ')
        if name == '':
            players.append(Player(colors[i], name=f'Игрок {i + 1}'))
        else:
            players.append(Player(colors[i], name=name))
    try:
        board_size = int(input('Выберите размер карты (1-3): '))
        assert 1 <= board_size <= 3
    except Exception:
        print('Введены неверные данный')
        sys.exit()

    width = height = (board_size + 2) * 10

    pygame.init()

    sprites = pygame.sprite.Group()
    units = pygame.sprite.Group()

    size = original_size = 15
    delta = original_delta = 5
    vertical_indent = horizontal_indent = 50

    board = None
    while not board:
        try:
            board = Board(width, height, size)
        except Exception:
            continue
    board_size = round(width * size * 3 ** 0.5), round(height * size * 1.5)
    board_width, board_height = board_size

    screen_size = round(width * size * 3 ** 0.5 + horizontal_indent * 2), \
                  round(height * size * 1.5 + vertical_indent * 2)
    screen_width, screen_height = screen_size
    screen = pygame.display.set_mode(screen_size, pygame.FULLSCREEN)
    screen.fill(color_water)
    fps = 60
    clock = pygame.time.Clock()
    camera = Camera()

    title3_font = pygame.freetype.Font('data/fonts/thintel.ttf', 24)
    title2_font = pygame.freetype.Font('data/fonts/thintel.ttf', 30)
    title1_font = pygame.freetype.Font('data/fonts/thintel.ttf', 36)
    title0_font = pygame.freetype.Font('data/fonts/thintel.ttf', 45)

    app = Application()
    app.start()
