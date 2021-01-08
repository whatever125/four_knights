import pygame
import random
import sys
from queue import PriorityQueue
from dataclasses import dataclass, field
from typing import Any

color_earth = (61, 152, 72)
color_earth_clicked = (38, 124, 48)
color_earth_highlighted = (92, 172, 101)

color_village = (166, 127, 67)
color_village_clicked = (139, 101, 43)
color_village_highlighted = (179, 149, 105)

color_water = (115, 170, 220)

offset_directions = [
    [[+1, 0], [0, -1], [-1, -1],
     [-1, 0], [-1, +1], [0, +1]],
    [[+1, 0], [+1, -1], [0, -1],
     [-1, 0], [0, +1], [+1, +1]],
]


def offset_neighbor(row, col, direction):
    parity = row % 2
    dir = offset_directions[parity][direction]
    return row + dir[1], col + dir[0]


def cube_to_offset(x, y, z):
    col = x + (z - (z % 2)) / 2
    row = z
    return col, row


def offset_to_cube(col, row):
    x = col - (row - (row % 2)) / 2
    z = row
    y = -x - z
    return x, y, z


def offset_to_pixel(col, row):
    x = size * 3 ** 0.5 * (col + 0.5 * (row % 2))
    y = size * 3 / 2 * row
    return int(x) + indent, int(y) + indent


class Application:
    def start(self):
        self.main()

    def main(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.terminate()
                    return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        board.get_click(event.pos)
                    if event.button == 4:
                        self.zoom_in()
                    if event.button == 5:
                        self.zoom_out()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
                        self.zoom_to_original_position()
                    if event.key == pygame.K_RETURN:
                        board.end_turn()
            screen.fill(color_water)
            camera.update()
            sprites.draw(screen)
            board.render()
            units.draw(screen)
            pygame.display.flip()
            clock.tick(fps)

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
    def terminate():
        pygame.quit()
        sys.exit()


class Board:
    def __init__(self, width, height, cell_size):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.board = [[Cell(i, j) for j in range(self.width)] for i in range(self.height)]
        self.players = [Player(color='#FF0000'), Player(color='#0000FF')]
        self.turn = 0
        self.units = [Unit((20, 20), self, player=self.players[0]), Unit((21, 21), self, player=self.players[1])]
        print(self.players[1].units is self.players[0].units)
        self.selected_unit = None
        self.clicked = ()
        self.generate_board()

    def end_turn(self):
        if self.turn == len(self.players) - 1:
            self.turn = 0
        else:
            self.turn += 1

    def generate_board(self):
        board_generator = BoardGenerator(self)
        board_generator.generate()

    def get_cell_vertices(self, col, row):
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

        return int(column), int(row)

    def get_click(self, mouse_pos):
        cell = self.get_cell(mouse_pos)
        x, y = cell
        if 0 <= x < self.height and 0 <= y < self.width:
            self.on_click(cell)

    def on_click(self, cell_coords):
        player = self.players[self.turn]
        self.clicked = cell_coords
        select = False
        if not self.selected_unit or int(
                self.find_path(cell_coords, self.selected_unit.coords)) != 1:
            for unit in player.units:
                if unit.coords == cell_coords and unit in player.units:
                    self.selected_unit = unit
                    select = True
        elif int(self.find_path(cell_coords, self.selected_unit.coords)) == 1:
            for unit in self.units:
                if unit.coords == cell_coords:
                    self.selected_unit.melee_attack(self.selected_unit.melee, unit)
                    self.selected_unit = None
                    self.clicked = None
                    return
        if self.board[cell_coords[1]][cell_coords[0]].region == 'water':
            self.selected_unit = None
        elif not select and self.selected_unit and \
                self.find_path(self.selected_unit.coords, cell_coords) <= self.selected_unit.speed:
            self.selected_unit.move_to(*cell_coords)
            self.selected_unit = None
            self.clicked = None

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
            neighbors = filter(lambda x: self.board[x[1]][x[0]].region != 'water',
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

    def update_cell_size(self):
        self.cell_size = size

    def update_cell_region(self, x, y, region):
        self.board[x][y].region = region

    def update_cells(self):
        for row in self.board:
            for cell in row:
                cell.update()

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
        self.number_of_castles = 2  # TODO Изменение количества замков
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
        mid_x = self.height // 2 - 1
        mid_y = self.width // 2 - 1
        mid_cell = mid_x, mid_y
        self.generator[mid_cell] = 'plain'
        self.update_neighbours(mid_cell, 100, 'water', 'pre_plain')
        for _ in range(self.number_of_earth_cells):
            neighbours = list(filter(lambda x: self.generator[x] == 'pre_plain', self.generator))
            neighbour = random.choice(neighbours)
            self.generator[neighbour] = 'plain'
            self.update_neighbours(neighbour, 40, 'water', 'pre_plain')
        self.delete_pre_cells()

    def generate_forest(self):
        available_cells = list(filter(lambda x: self.generator[x] == 'plain', self.generator))
        first_cell = random.choice(available_cells)
        self.generator[first_cell] = 'forest'
        self.update_neighbours(first_cell, 100, 'plain', 'pre_forest')
        number_of_forest_cells = random.randint(self.min_region_cells, self.max_region_cells)
        for _ in range(number_of_forest_cells):
            try:
                available_cells = list(
                    filter(lambda x: self.generator[x] == 'pre_forest', self.generator))
                forest_cell = random.choice(available_cells)
                self.generator[forest_cell] = 'forest'
                self.update_neighbours(forest_cell, self.region_chance, 'plain', 'pre_forest')
            except Exception:
                pass
        self.delete_pre_cells()

    def generate_desert(self):
        available_cells = list(filter(lambda x: self.generator[x] == 'plain', self.generator))
        first_cell = random.choice(available_cells)
        self.generator[first_cell] = 'desert'
        self.update_neighbours(first_cell, 100, 'plain', 'pre_desert')
        number_of_desert_cells = random.randint(self.min_region_cells, self.max_region_cells)
        for _ in range(number_of_desert_cells):
            try:
                available_cells = list(
                    filter(lambda x: self.generator[x] == 'pre_desert', self.generator))
                forest_cell = random.choice(available_cells)
                self.generator[forest_cell] = 'desert'
                self.update_neighbours(forest_cell, self.region_chance, 'plain', 'pre_desert')
            except Exception:
                pass
        self.delete_pre_cells()

    def generate_mountain(self):
        available_cells = list(filter(lambda x: self.generator[x] == 'plain', self.generator))
        first_cell = random.choice(available_cells)
        self.generator[first_cell] = 'mountains'
        self.update_neighbours(first_cell, 100, 'plain', 'pre_mountain')
        number_of_mountain_cells = random.randint(self.min_region_cells, self.max_region_cells)
        for _ in range(number_of_mountain_cells):
            try:
                available_cells = list(
                    filter(lambda x: self.generator[x] == 'pre_mountain', self.generator))
                forest_cell = random.choice(available_cells)
                self.generator[forest_cell] = 'mountains'
                self.update_neighbours(forest_cell, self.region_chance, 'plain', 'pre_mountain')
            except Exception:
                pass
        self.delete_pre_cells()

    def generate_swamp(self):
        available_cells = list(filter(lambda x: self.generator[x] == 'plain', self.generator))
        first_cell = random.choice(available_cells)
        self.generator[first_cell] = 'swamp'
        self.update_neighbours(first_cell, 100, 'plain', 'pre_swamp')
        number_of_swamp_cells = random.randint(self.min_region_cells, self.max_region_cells)
        for _ in range(number_of_swamp_cells):
            try:
                available_cells = list(
                    filter(lambda x: self.generator[x] == 'pre_swamp', self.generator))
                forest_cell = random.choice(available_cells)
                self.generator[forest_cell] = 'swamp'
                self.update_neighbours(forest_cell, self.region_chance, 'plain', 'pre_swamp')
            except Exception:
                pass
        self.delete_pre_cells()

    def generate_villages(self):
        for _ in range(self.number_of_villages):
            available_cells = list(filter(lambda x: self.generator[x] != 'water', self.generator))
            village_cell = random.choice(available_cells)
            self.generator[village_cell] = 'village'

    def generate_castles(self):
        for _ in range(self.number_of_castles):
            available_cells = list(filter(lambda x: self.generator[x] != 'water', self.generator))
            castle_cell = random.choice(available_cells)
            self.generator[castle_cell] = 'castle'

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
    def __init__(self, color='#FF0000', money=0, name='Игрок'):
        self.color = color
        self.units = []
        self.money = money
        self.name = name

    def delete_unit(self, unit):
        self.units = list(filter(lambda x: x != unit, self.units))

    def add_unit(self, unit):
        self.units.append(unit)

class Cell:
    def __init__(self, col, row, region='plain'):
        self.region = region
        self.col = col
        self.row = row
        self.coords = (row, col)
        self.cube = offset_to_cube(col, row)
        self.x, self.y, self.z = self.cube

    def load_sprite(self):
        self.sprite = pygame.sprite.Sprite()
        if self.region == 'castle':
            self.image = pygame.image.load(f'data/{self.region}{random.randint(1, 1)}.png')
        else:
            self.image = pygame.image.load(f'data/{self.region}{random.randint(1, 1)}.png')
        self.sprite.image = pygame.transform.scale(self.image,
                                                   (round(size * 3 ** 0.5) + 2, round(size * 2) + 2))
        self.sprite.rect = self.sprite.image.get_rect()
        pixel = offset_to_pixel(*self.coords)
        self.sprite.rect.x = pixel[0]
        self.sprite.rect.y = pixel[1]
        sprites.add(self.sprite)

    def update(self):
        sprites.remove(self.sprite)
        self.sprite.image = pygame.transform.scale(self.image,
                                                   (round(size * 3 ** 0.5) + 2, round(size * 2) + 2))
        self.sprite.rect = self.sprite.image.get_rect()
        pixel = offset_to_pixel(*self.coords)
        self.sprite.rect.x = pixel[0] + camera.dx
        self.sprite.rect.y = pixel[1] + camera.dy
        sprites.add(self.sprite)

    def move_sprite(self, dx, dy):
        self.sprite.rect.x += dx
        self.sprite.rect.y += dy


class Unit:
    def __init__(self, coords, board, hp=20, speed=6, sprite='default',
                 melee={'damage': 10, 'attacks': 1, 'mod': 0, 'type': 'melee'}, ranged=None, player=None):
        self.coords = coords
        self.board = board
        self.hp = hp
        self.speed = speed
        self.melee = melee
        self.ranged = ranged
        self.defence = 0.5
        self.load_sprite(sprite)
        self.player = player
        if self.player:
            player.add_unit(self)

    def load_sprite(self, sprite):
        self.sprite = pygame.sprite.Sprite()
        self.image = pygame.image.load(f'{sprite}.png')
        self.sprite.image = pygame.transform.scale(self.image, (int(size * 2), int(size * 2)))
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

    def update(self):
        units.remove(self.sprite)
        self.sprite.image = pygame.transform.scale(self.image,
                                                   (int(size * 2), int(size * 2)))
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

        if self.mouse_is_on_the_right():
            self.move_camera_to_the_left()

        if self.mouse_is_at_the_bottom():
            self.move_camera_to_the_top()

        if self.mouse_is_at_the_top():
            self.move_camera_to_the_bottom()

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
    board = Board(width, height, size)
    screen_size = screen_width, screen_height = round(width * size * 3 ** 0.5 + indent * 2), \
                                                round(height * size * 1.5 + indent * 2)
    screen = pygame.display.set_mode(screen_size)
    screen.fill(color_water)
    fps = 60
    clock = pygame.time.Clock()
    camera = Camera()

    app = Application()
    app.start()
