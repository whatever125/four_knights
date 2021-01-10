import pygame
import pygame.freetype
import random
import sys
from queue import PriorityQueue
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
    {'name': 'Тяжелый пехотинец',
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
    return int(x) + indent, int(y) + indent


class Application:
    def __init__(self):
        self.button_end_turn = pygame.Rect(600, 600, 100, 30)  # TODO изменить положение кнопки
        self.rent_unit_surface = None
        self.rent_unit_coords = None

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
                        elif self.rent_unit_surface and pygame.Rect(*self.rent_unit_coords, 600,
                                                                    600).collidepoint(mouse_pos):
                            self.rent_unit(mouse_pos)
                            self.hide_information()
                        else:
                            board.get_click(event.pos)
                            self.hide_information()
                    if event.button == 3 and board.is_players_castle(event.pos):
                        self.selected_castle = board.get_cell(event.pos)
                        self.show_rent_unit()
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
            screen.fill(color_water)
            camera.update()
            board.render()
            sprites.draw(screen)
            units.draw(screen)
            pygame.draw.rect(screen, (0, 0, 0),
                             self.button_end_turn)  # TODO изменить цвет, добавить надпись
            if self.rent_unit_surface:
                screen.blit(self.rent_unit_surface, self.rent_unit_coords)
            pygame.display.flip()
            clock.tick(fps)

    def show_rent_unit(self):
        self.rent_unit_surface = pygame.Surface((600, 600))
        self.rent_unit_surface.fill((0, 0, 0))
        self.rent_unit_surface.set_alpha(210)
        display_width, display_height = pygame.display.get_surface().get_size()
        self.rent_unit_coords = (display_width - 600) // 2, (display_height - 600) // 2
        for i in range(len(all_units)):
            lines = []
            for inf in all_units[i]:
                line = inf
                line += ': '
                line += str(all_units[i][inf])
                lines.append(line)
            for j in range(len(lines)):
                information_font.render_to(self.rent_unit_surface,
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
        neighbors = filter(lambda x: board.board[x[0]][x[1]].region != 'water',
                           [offset_neighbor(*coords, i) for i in range(6)])
        for i in neighbors:
            f = False
            for j in board.units:
                if j.coords == i:
                    f = True
            if not f and player.money >= int(unit['cost']):
                melee = unit['attacks'][0].split('x')
                ranged = unit['attacks'][0].split('x')
                unit = Unit(i, board, name=unit['name'], cost=unit['cost'], sprite=unit['sprite'],
                            hp=unit['hp'],
                            speed=unit['speed'], player=player,
                            melee={'type': 'melee', 'attacks': int(melee[0]),
                                   'damage': int(melee[1]), 'mod': 0},
                            ranged={'type': 'ranged', 'attacks': int(ranged[0]),
                                    'damage': int(ranged[1]), 'mod': 0})
                player.add_unit(unit)
                board.units.append(unit)
                board.update_units()
                player.money -= int(unit.cost)
                break

    def hide_information(self):
        self.rent_unit_surface = None
        self.rent_unit_coords = None
        self.selected_castle = None

    @staticmethod
    def zoom_in():
        global size, delta, screen_width, screen_height
        if round(size * 1.1) <= 50:
            size = round(size * 1.1)
            delta = round(delta * 1.1)
            screen_width = round(screen_width * 1.1)
            screen_height = round(screen_height * 1.1)
            camera.dx = round(camera.dx * 1.1 - screen_size[0] * 0.05)
            camera.dy = round(camera.dy * 1.1 - screen_size[1] * 0.05)
            board.update_cell_size()
            board.update_units()
            board.update_cells()

    @staticmethod
    def zoom_out():
        global size, delta, screen_width, screen_height
        if round(size / 1.1) >= 10:
            size = round(size / 1.1)
            delta = round(delta / 1.1)
            screen_width = round(screen_width / 1.1)
            screen_height = round(screen_height / 1.1)
            camera.dx = round(camera.dx / 1.1 + screen_size[0] * 0.045)
            camera.dy = round(camera.dy / 1.1 + screen_size[1] * 0.045)
            board.update_cell_size()
            board.update_units()
            board.update_cells()

    @staticmethod
    def zoom_to_original_position():
        global size, delta, screen_width, screen_height
        camera.dx = 0
        camera.dy = 0
        size = original_size
        delta = original_delta
        screen_width = screen_size[0]
        screen_height = screen_size[1]
        board.update_cell_size()
        board.update_units()
        board.update_cells()

    @staticmethod
    def end_turn():
        global turn
        board.make_cells_available()
        if not players[turn].units and not players[turn].castles:
            del players[turn]
            if turn > 0:
                turn -= 1
        if turn == len(players) - 1:
            turn = 0
        else:
            turn += 1
        players[turn].money += (
                    players[turn].income + len(players[turn].villages) - len(players[turn].units))

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
        self.units = [
            Unit(players[0].castles[0].coords, self, player=players[0], name='Герменита',
                 sprite='nita', hp=50, speed=6,
                 cost=0, melee={'damage': 5, 'attacks': 4, 'mod': 10, 'type': 'melee'},
                 ranged={'damage': 10, 'attacks': 1, 'mod': 0, 'type': 'ranged'}),
            Unit(players[1].castles[0].coords, self, player=players[1], name='Афина', sprite='nana',
                 hp=30, speed=7,
                 cost=0, melee={'damage': 5, 'attacks': 1, 'mod': 0, 'type': 'melee'},
                 ranged={'damage': 15, 'attacks': 2, 'mod': 10, 'type': 'ranged'})]

    def generate_board(self):
        board_generator = BoardGenerator(self)
        board_generator.generate()

    def get_cell_vertices(self, row, col):
        x = self.cell_size * 3 ** 0.5 * (col + 0.5 * (row % 2))
        y = self.cell_size * 1.5 * row
        return (int(x + 3 ** 0.5 * self.cell_size / 2) + indent + camera.dx,
                int(y) + indent + camera.dy), \
               (int(x + 3 ** 0.5 * self.cell_size) + indent + camera.dx,
                int(y + 0.5 * self.cell_size) + indent + camera.dy), \
               (int(x + 3 ** 0.5 * self.cell_size) + indent + camera.dx,
                int(y + 1.5 * self.cell_size) + indent + camera.dy), \
               (int(x + 3 ** 0.5 * self.cell_size / 2) + indent + camera.dx,
                int(y + 2 * self.cell_size) + indent + camera.dy), \
               (int(x) + indent + camera.dx,
                int(y + 1.5 * self.cell_size) + indent + camera.dy), \
               (int(x) + indent + camera.dx,
                int(y + 0.5 * self.cell_size) + indent + camera.dy)

    def render(self):
        for row in self.board:
            for cell in row:
                cell.update()

    def get_cell(self, mouse_pos):
        x, y = mouse_pos
        x -= indent
        x -= camera.dx
        y -= indent
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
                            self.board[clicked_row][clicked_col], unit.speed)
                        self.make_cells_available(*available_cells)
                    else:
                        self.selected_unit = None
                        self.make_cells_available()
        elif self.distance(self.selected_unit.coords, clicked_cell) == 1:
            for unit in self.units:
                if unit.coords == clicked_cell:
                    if unit not in player.units:
                        self.make_cells_available()
                        self.selected_unit.melee_attack(self.selected_unit.melee, unit)
                        self.selected_unit = None
                        return
                    else:
                        self.selected_unit = unit
                        just_selected = True
                        self.make_cells_unavailable()
                        available_cells = self.cells_available_from(
                            self.board[clicked_row][clicked_col], unit.speed)
                        self.make_cells_available(*available_cells)
        if self.board[clicked_row][clicked_col].region == 'water':
            self.selected_unit = None
            self.make_cells_available()
        elif not just_selected and self.selected_unit and self.board[clicked_row][clicked_col] \
                in self.cells_available_from(self.board[self.selected_unit.coords[0]][
                                                 self.selected_unit.coords[1]],
                                             self.selected_unit.speed):
            self.make_cells_available()
            self.selected_unit.move_to(*clicked_cell)
            self.selected_unit = None

    def find_path(self, start, goal):
        frontier = PriorityQueue()
        frontier.put(PrioritizedItem(0, start))
        came_from = dict()
        cost_so_far = dict()
        came_from[start] = None
        cost_so_far[start] = 0
        while not frontier.empty():
            current = frontier.get().item
            if current == goal:
                return cost_so_far[current]
            neighbors = filter(lambda x: self.board[x[0]][x[1]].region != 'water',
                               [offset_neighbor(*current, i) for i in range(6)])
            for next in neighbors:
                new_cost = cost_so_far[current] + self.distance(current, next)
                if next not in cost_so_far or new_cost < cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + self.distance(next, goal)
                    frontier.put(PrioritizedItem(priority, next))
                    came_from[next] = current

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

    def is_unit(self, mouse_pos):
        cell = self.get_cell(mouse_pos)
        for unit in self.units:
            if unit.coords == cell:
                return True
        return False

    def update_cell_size(self):
        self.cell_size = size

    def update_cell_region(self, x, y, region):
        self.board[x][y].region = region

    def update_cells(self):
        for row in self.board:
            for cell in row:
                cell.update()

    def make_cells_available(self, *cells):
        if cells:
            for cell in cells:
                cell.available = True
        else:
            for row in self.board:
                for cell in row:
                    cell.available = True

    def make_cells_unavailable(self, *cells):
        if cells:
            for cell in cells:
                cell.available = False
        else:
            for row in self.board:
                for cell in row:
                    cell.available = False

    def move_cells(self, dx, dy):
        for row in self.board:
            for cell in row:
                cell.move_sprite(dx, dy)

    def update_units(self):
        for unit in self.units:
            unit.update()

    def move_units(self, dx, dy):
        for unit in self.units:
            unit.move_sprite(dx, dy)

    def delete_unit(self, unit):
        self.units = list(filter(lambda x: x != unit, self.units))


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
    def __init__(self, color='red', money=100, income=5, name='Игрок'):
        self.color = color
        self.units = []
        self.villages = []
        self.castles = []
        self.money = money
        self.name = name
        self.income = income

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
            self.image_available = pygame.image.load(f'data/{self.region}_{self.player.color}.png')
            self.image_unavailable = pygame.image.load(
                f'data/{self.region}_{self.player.color}_unavailable.png')
        else:
            self.image_available = pygame.image.load(f'data/{self.region}{self.num}.png')
            self.image_unavailable = pygame.image.load(
                f'data/{self.region}{self.num}_unavailable.png')
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
    def __init__(self, coords, board, hp=20, speed=6, cost=15, sprite='default', name='Рыцарь',
                 melee={'damage': 10, 'attacks': 1, 'mod': 0, 'type': 'melee'}, ranged=None,
                 player=None):
        self.coords = coords
        self.board = board
        self.hp = hp
        self.speed = speed
        self.cost = cost
        self.name = name
        self.melee = melee
        self.ranged = ranged
        self.defence = 0.5
        self.player = player
        if self.player:
            self.player.add_unit(self)
        self.sprite_name = sprite
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
        elif (self.board.board[x][y].captured) and (self.board.board[x][y].region == 'village'):
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
        for i in range(attack['attacks']):
            if random.random() + attack['mod'] > enemy.defence:
                enemy.take_damage(attack['damage'])
                print(self.hp, enemy.hp)
                if enemy.hp <= 0:
                    enemy.die()
                    return
        if enemy.melee:
            for i in range(enemy.melee['attacks']):
                if random.random() + enemy.melee['mod'] > self.defence:
                    self.take_damage(enemy.melee['damage'])
                    print(self.hp, enemy.hp)
                    if self.hp <= 0:
                        self.die()
                        return

    def ranged_attack(self, attack, enemy):
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

    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    def update(self):
        if self.mouse_is_on_the_left():
            self.move_camera_to_the_right()
            app.hide_information()

        if self.mouse_is_on_the_right():
            self.move_camera_to_the_left()
            app.hide_information()

        if self.mouse_is_at_the_bottom():
            self.move_camera_to_the_top()
            app.hide_information()

        if self.mouse_is_at_the_top():
            self.move_camera_to_the_bottom()
            app.hide_information()

    @staticmethod
    def mouse_is_on_the_left():
        x, y = pygame.mouse.get_pos()
        return x <= screen_size[0] * 0.1 and x != 0 and y != 0 and \
               x != screen_size[0] - 1 and y != screen_size[1] - 1

    @staticmethod
    def mouse_is_on_the_right():
        x, y = pygame.mouse.get_pos()
        return x >= screen_size[0] * 0.9 and x != 0 and y != 0 and \
               x != screen_size[0] - 1 and y != screen_size[1] - 1

    @staticmethod
    def mouse_is_at_the_bottom():
        x, y = pygame.mouse.get_pos()
        return y <= screen_size[1] * 0.1 and x != 0 and y != 0 and \
               x != screen_size[0] - 1 and y != screen_size[1] - 1

    @staticmethod
    def mouse_is_at_the_top():
        x, y = pygame.mouse.get_pos()
        return y >= screen_size[1] * 0.9 and x != 0 and y != 0 and \
               x != screen_size[0] - 1 and y != screen_size[1] - 1

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


if __name__ == '__main__':
    pygame.init()
    sprites = pygame.sprite.Group()
    units = pygame.sprite.Group()
    width = 30
    height = 30
    size = original_size = 15
    delta = original_delta = 4
    indent = 50

    players = [Player(color='red'), Player(color='blue')]
    turn = 0

    board = Board(width, height, size)
    screen_size = screen_width, screen_height = round(width * size * 3 ** 0.5 + indent * 2), \
                                                round(height * size * 1.5 + indent * 2)
    screen = pygame.display.set_mode(screen_size)
    screen.fill(color_water)
    fps = 60
    clock = pygame.time.Clock()
    camera = Camera()

    information_font = pygame.freetype.Font('data/fonts/thintel.ttf', 24)

    app = Application()
    app.start()
