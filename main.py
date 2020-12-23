from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import random

color_earth = (61, 152, 72)
color_earth_clicked = (38, 124, 48)
color_earth_highlighted = (92, 172, 101)

color_village = (166, 127, 67)
color_village_clicked = (139, 101, 43)
color_village_highlighted = (179, 149, 105)

color_water = (175, 217, 216)


class Cell:
    def __init__(self, col, row, cell_type='water'):
        self.type = cell_type
        self.col = col
        self.row = row
        self.coords = (row, col)
        self.cube = offset_to_cube(col, row)
        self.x, self.y, self.z = self.cube


class Board:
    def __init__(self, width, height, cell_size, indent):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.indent = indent
        self.board = [[Cell(i, j) for j in range(self.width)] for i in range(self.height)]
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
        return (int(x + 3 ** 0.5 * self.cell_size / 2) + self.indent, int(y) + self.indent), \
               (int(x + 3 ** 0.5 * self.cell_size) + self.indent, int(y + 0.5 * self.cell_size) +
                self.indent), \
               (int(x + 3 ** 0.5 * self.cell_size) + self.indent, int(y + 1.5 * self.cell_size) +
                self.indent), \
               (int(x + 3 ** 0.5 * self.cell_size / 2) + self.indent, int(y + 2 * self.cell_size) +
                self.indent), \
               (int(x) + self.indent, int(y + 1.5 * self.cell_size) + self.indent), \
               (int(x) + self.indent, int(y + 0.5 * self.cell_size) + self.indent)

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
        y -= self.indent
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

    def get_click(self, mouse_pos):
        cell = self.get_cell(mouse_pos)
        x, y = cell
        if 0 <= x < self.height and 0 <= y < self.width:
            self.on_click(cell)


offset_directions = [
    [[+1, 0], [0, -1], [-1, -1],
     [-1, 0], [-1, +1], [0, +1]],
    [[+1, 0], [+1, -1], [0, -1],
     [-1, 0], [0, +1], [+1, +1]],
]


def offset_to_pixel(col, row, size):
    x = size * 3 ** 0.5 * (col + 0.5 * (row % 2))
    y = size * 3/2 * row
    return int(x), int(y)


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
    return max(abs(a.x - b.x), abs(a.y - b.y), abs(a.z - b.z))


if __name__ == '__main__':
    pygame.init()

    width = 50
    height = 50
    size = 10
    indent = 50
    board = Board(width, height, size, indent)

    size = int(width * size * 3 ** 0.5 + indent * 2), int(height * size * 1.5 + indent * 2)
    screen = pygame.display.set_mode(size)
    screen.fill(color_water)

    fps = 60
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                board.get_click(event.pos)
        screen.fill(color_water)
        board.render()
        pygame.display.flip()
        clock.tick(fps)
