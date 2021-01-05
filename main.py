from os import environ

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import random
from queue import PriorityQueue
from dataclasses import dataclass, field
from typing import Any
import random

color_earth = (61, 152, 72)
color_earth_clicked = (38, 124, 48)
color_earth_highlighted = (92, 172, 101)

color_village = (166, 127, 67)
color_village_clicked = (139, 101, 43)
color_village_highlighted = (179, 149, 105)

color_water = (175, 217, 216)


@dataclass(order=True)
class PrioritizedItem:
    priority: int
    item: Any=field(compare=False)

class Camera:
    def __init__(self):
        self.dx, self.dy = 0, 0

    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    def update(self):
        x, y = pygame.mouse.get_pos()
        if x <= screen_size[0] * 0.1 and x != 0 and y != 0 and \
                x != screen_size[0] - 1 and y != screen_size[1] - 1:
            self.dx += delta
            for unit in board.units:
                unit.sprite.rect.x += delta
        if y <= screen_size[1] * 0.1 and x != 0 and y != 0 and \
                x != screen_size[0] - 1 and y != screen_size[1] - 1:
            self.dy += delta
            for unit in board.units:
                unit.sprite.rect.y += delta
        if x >= screen_size[0] * 0.9 and x != 0 and y != 0 and \
                x != screen_size[0] - 1 and y != screen_size[1] - 1:
            self.dx -= delta
            for unit in board.units:
                unit.sprite.rect.x -= delta
        if y >= screen_size[1] * 0.9 and x != 0 and y != 0 and \
                x != screen_size[0] - 1 and y != screen_size[1] - 1:
            self.dy -= delta
            for unit in board.units:
                unit.sprite.rect.y -= delta


class Cell:
    def __init__(self, col, row, cell_type='water'):
        self.type = cell_type
        self.col = col
        self.row = row
        self.coords = (row, col)
        self.cube = offset_to_cube(col, row)
        self.x, self.y, self.z = self.cube


class Unit:
    def __init__(self, coords, board, hp=20, speed=6, sprite='default', melee={'damage': 10, 'attacks': 1, 'mod': 0, 'type': 'melee'}, ranged=None):
        self.hp = hp
        self.speed = speed
        self.defence = 0.5
        self.sprite = pygame.sprite.Sprite()
        self.image = pygame.image.load(f'{sprite}.png')
        self.sprite.image = pygame.transform.scale(self.image, (int(size * 2), int(size * 2)))
        self.sprite.rect = self.sprite.image.get_rect()
        pixel = offset_to_pixel(cell.coords[0], cell.coords[1])
        self.sprite.rect.x = pixel[0]
        self.sprite.rect.y = pixel[1]
        sprites.add(self.sprite)
        self.melee = melee
        self.ranged = ranged
        self.coords = coords
        self.board = board

    def move(self, x, y):
        self.coords = (x, y)
        pixel = offset_to_pixel(self.coords[0], self.coords[1])
        self.sprite.rect.x = pixel[0] + camera.dx
        self.sprite.rect.y = pixel[1] + camera.dy

    def die(self):
        self.board.units = list(filter(lambda x:x != self, self.board.units))
        sprites.remove(self.sprite)

    def attack(self, attack, enemy):
        if attack['type'] == 'melee':
            for i in range(attack['attacks']):
                if random.random() + attack['mod'] > enemy.defence:
                    enemy.hp -= attack['damage']
                    print(self.hp, enemy.hp)
                    if enemy.hp <= 0:
                        enemy.die()
                        return
            if enemy.melee:
                for i in range(enemy.melee['attacks']):
                    if random.random() + enemy.melee['mod'] > self.defence:
                        self.hp -= enemy.melee['damage']
                        print(self.hp, enemy.hp)
                        if self.hp <= 0:
                            self.die()
                            return
        if attack['type'] == 'ranged':
            for i in range(attack['attacks']):
                if random.random() + attack['mod'] > enemy.defence:
                    enemy.hp -= attack['damage']
                    if enemy.hp <= 0:
                        enemy.die()
                        return
            if enemy.ranged:
                for i in range(enemy.ranged['attacks']):
                    if random.random() + enemy.ranged['mod'] > self.defence:
                        self.hp -= enemy.ranged['damage']
                        if self.hp <= 0:
                            self.die()
                            return


    def update(self):
        sprites.remove(self.sprite)
        self.sprite.image = pygame.transform.scale(self.image,
                                                   (int(size * 2), int(size * 2)))
        self.sprite.rect = self.sprite.image.get_rect()
        pixel = offset_to_pixel(self.coords[0], self.coords[1])
        self.sprite.rect.x = pixel[0] + camera.dx
        self.sprite.rect.y = pixel[1] + camera.dy
        sprites.add(self.sprite)


class Board:
    def __init__(self, width, height, cell_size, indent):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.indent = indent
        self.board = [[Cell(i, j) for j in range(self.width)] for i in range(self.height)]
        self.units = [Unit(self.board[10][10], 10, 5), Unit(self.board[15][15], 10, 5)]
        self.selected_unit = None
        self.clicked = ()
        self.generate_board()
        self.generate_village()

    def generate_board(self):
        generator = {(i, j): 0 for i in range(self.height) for j in range(self.width)}
        x, y = self.height // 2 - 1, self.width // 2 - 1
        generator[(x, y)] = 2
        for direct in range(6):
            try:
                y1, x1 = offset_neighbor(y, x, direct)
                generator[(x1, y1)] = 1
            except Exception:
                pass
        for _ in range((self.width * self.height) // 2):
            friends = list(filter(lambda x: generator[x] == 1, generator))
            friend = random.choice(friends)
            generator[friend] = 2
            for direct in range(6):
                try:
                    y1, x1 = offset_neighbor(friend[1], friend[0], direct)
                    if generator[(x1, y1)] == 0 and random.randint(0, 100) < 40:
                        generator[(x1, y1)] = 1
                except Exception:
                    pass
        for i in generator:
            try:
                assert 0 <= i[0] < self.height
                assert 0 <= i[1] < self.width
                if generator[i] == 2:
                    self.board[i[0]][i[1]].type = 'earth'
            except Exception:
                pass

    def generate_village(self):
        generator = {(i, j): self.board[i][j].type == 'earth' for i in range(self.height) for j in
                     range(self.width)}
        for _ in range((self.width * self.height) // 100):
            earth = list(filter(lambda x: generator[x] == 1, generator))
            village = random.choice(earth)
            generator[village] = 2
        for i in generator:
            if generator[i] == 2:
                self.board[i[0]][i[1]].type = 'village'

    def offset_to_pixel(self, col, row):
        x = self.cell_size * 3 ** 0.5 * (col + 0.5 * (row % 2))
        y = self.cell_size * 1.5 * row
        return (int(x + 3 ** 0.5 * self.cell_size / 2) + self.indent + camera.dx,
                int(y) + self.indent + camera.dy), \
               (int(x + 3 ** 0.5 * self.cell_size) + self.indent + camera.dx,
                int(y + 0.5 * self.cell_size) + self.indent + camera.dy), \
               (int(x + 3 ** 0.5 * self.cell_size) + self.indent + camera.dx,
                int(y + 1.5 * self.cell_size) + self.indent + camera.dy), \
               (int(x + 3 ** 0.5 * self.cell_size / 2) + self.indent + camera.dx,
                int(y + 2 * self.cell_size) + self.indent + camera.dy), \
               (int(x) + self.indent + camera.dx,
                int(y + 1.5 * self.cell_size) + self.indent + camera.dy), \
               (int(x) + self.indent + camera.dx,
                int(y + 0.5 * self.cell_size) + self.indent + camera.dy)

    def render(self):
        for row in self.board:
            for cell in row:
                if cell.type == 'earth':
                    if cell.coords == self.clicked:
                        pygame.draw.polygon(screen, color_earth_clicked,
                                            self.offset_to_pixel(*cell.coords), 0)
                    else:
                        pygame.draw.polygon(screen, color_earth,
                                            self.offset_to_pixel(*cell.coords), 0)
                elif cell.type == 'village':
                    if cell.coords == self.clicked:
                        pygame.draw.polygon(screen, color_village_clicked,
                                            self.offset_to_pixel(*cell.coords), 0)
                    else:
                        pygame.draw.polygon(screen, color_village,
                                            self.offset_to_pixel(*cell.coords), 0)
                if cell.type != 'water':
                    pygame.draw.polygon(screen, color_earth_clicked,
                                        self.offset_to_pixel(*cell.coords), 1)

    def get_cell(self, mouse_pos):
        x, y = mouse_pos
        x -= self.indent
        x -= camera.dx
        y -= self.indent
        y -= camera.dy
        gridHeight = self.cell_size * 1.5
        gridWidth = self.cell_size * 3 ** 0.5
        halfWidth = gridWidth / 2
        c = 0.5 * self.cell_size
        m = c / halfWidth
        row = y // gridHeight
        rowIsOdd = row % 2 == 1

        if rowIsOdd:
            column = (x - halfWidth) // gridWidth
        else:
            column = x // gridWidth
        relY = y - (row * gridHeight)

        if rowIsOdd:
            relX = (x - (column * gridWidth)) - halfWidth
        else:
            relX = x - (column * gridWidth)
        if relY < (-m * relX) + c:
            row -= 1
            if not rowIsOdd:
                column -= 1
        elif relY < (m * relX) - c:
            row -= 1
            if rowIsOdd:
                column += 1

        return int(column), int(row)

    def on_click(self, cell_coords):
        self.clicked = cell_coords
        select = False
        if not self.selected_unit or int(self.find_path(cell_coords, self.selected_unit.coords)) != 1:
            for i in self.units:
                if i.coords == cell_coords:
                    self.selected_unit = i
                    select = True
        elif int(self.find_path(cell_coords, self.selected_unit.coords)) == 1:
            for i in self.units:
                if i.coords == cell_coords:
                    self.selected_unit.attack(self.selected_unit.melee, i)
                    self.selected_unit = None
                    self.clicked = None
                    return
        if self.board[cell_coords[1]][cell_coords[0]].type == 'water':
            self.selected_unit = None
        elif not select and self.selected_unit and self.find_path(self.selected_unit.coords, cell_coords) <= self.selected_unit.speed:
            self.selected_unit.move(*cell_coords)
            self.selected_unit = None

    def get_click(self, mouse_pos):
        cell = self.get_cell(mouse_pos)
        x, y = cell
        if 0 <= x < self.height and 0 <= y < self.width:
            self.on_click(cell)

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
            neighbors = filter(lambda x:self.board[x[1]][x[0]].type != 'water',[offset_neighbor(current[0], current[1], i) for i in range(6)])
            for next in neighbors:
                new_cost = cost_so_far[current] + distance(current, next)
                if next not in cost_so_far or new_cost < cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + distance(next, goal)
                    frontier.put(PrioritizedItem(priority, next))
                    came_from[next] = current
    def update(self):
        self.cell_size = size


offset_directions = [
    [[+1, 0], [0, -1], [-1, -1],
     [-1, 0], [-1, +1], [0, +1]],
    [[+1, 0], [+1, -1], [0, -1],
     [-1, 0], [0, +1], [+1, +1]],
]


def offset_to_pixel(col, row):
    x = size * 3 ** 0.5 * (col + 0.5 * (row % 2))
    y = size * 3 / 2 * row
    return int(x) + indent, int(y) + indent


def offset_neighbor(col, row, direction):
    parity = row % 2
    dir = offset_directions[parity][direction]
    return col + dir[0], row + dir[1]


def cube_to_offset(x, y, z):
    col = x + (z - (z % 2)) / 2
    row = z
    return col, row


def offset_to_cube(col, row):
    x = col - (row - (row % 2)) / 2
    z = row
    y = -x - z
    return x, y, z


def distance(a, b):
    return (abs(a[0] - b[0])
          + abs(a[0] + a[1] - b[0] - b[1])
          + abs(a[1] - b[1])) / 2


if __name__ == '__main__':
    pygame.init()
    sprites = pygame.sprite.Group()
    width = 30
    height = 30
    size = original_size = 15
    delta = original_delta = 3
    indent = 50
    board = Board(width, height, size, indent)

    screen_size = screen_width, screen_height = round(width * size * 3 ** 0.5 + indent * 2), \
                                                round(height * size * 1.5 + indent * 2)
    screen = pygame.display.set_mode(screen_size)
    screen.fill(color_water)
    fps = 60
    clock = pygame.time.Clock()

    camera = Camera()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    board.get_click(event.pos)
                if event.button == 4:
                    if round(size * 1.1) <= 50:
                        size = round(size * 1.1)
                        delta = round(delta * 1.1)
                        screen_width = round(screen_width * 1.1)
                        screen_height = round(screen_height * 1.1)
                        camera.dx = round(camera.dx * 1.1 - screen_size[0] * 0.05)
                        camera.dy = round(camera.dy * 1.1 - screen_size[1] * 0.05)
                        board.update()
                        for unit in board.units:
                            unit.update()
                if event.button == 5:
                    if round(size / 1.1) >= 10:
                        size = round(size / 1.1)
                        delta = round(delta / 1.1)
                        screen_width = round(screen_width / 1.1)
                        screen_height = round(screen_height / 1.1)
                        camera.dx = round(camera.dx / 1.1 + screen_size[0] * 0.045)
                        camera.dy = round(camera.dy / 1.1 + screen_size[1] * 0.045)
                        board.update()
                        for unit in board.units:
                            unit.update()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z:
                    camera.dx = 0
                    camera.dy = 0
                    size = original_size
                    delta = original_delta
                    screen_width = screen_size[0]
                    screen_height = screen_size[1]
                    board.update()
                    for unit in board.units:
                        unit.update()
        screen.fill(color_water)
        camera.update()
        board.render()
        sprites.draw(screen)
        pygame.display.flip()
        clock.tick(fps)
