import pygame
import random

WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 895, 670
FPS = 13
TILE_SIZE = 32
ENEMY_EVENT = 30
intro_text = ["Игра лабиринт",
              "ЦЕЛЬ:",
              "Спастись и добраться до синего выхода",
              "ПРАВИЛА:",
              "Управляйте с помощью стрелок на клавиатуре",
              "Для начала игры нажмите любую кнопку"]

gravity = 0.25
screen_rect = (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
pygame.init()
all_sprites = pygame.sprite.Group()
clock = pygame.time.Clock()
screen = pygame.display.set_mode(WINDOW_SIZE)
count = 2


def load_image(name, color_key=None):  # загрузка картинок
    try:
        image = pygame.image.load(name).convert()
    except pygame.error as message:
        print('Cannot load image:', name)
        raise SystemExit(message)

    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


class Particle(pygame.sprite.Sprite):  # создание частиц
    fire = [load_image("star.png")]
    for scale in (2, 5, 10):
        fire.append(pygame.transform.scale(fire[0], (scale, scale)))

    def __init__(self, pos, dx, dy):
        super().__init__(all_sprites)
        self.image = random.choice(self.fire)
        self.rect = self.image.get_rect()

        self.velocity = [dx, dy]
        self.rect.x, self.rect.y = pos

        self.gravity = gravity

    def update(self):
        self.velocity[1] += self.gravity
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        if not self.rect.colliderect(screen_rect):
            self.kill()


def terminate():
    pygame.quit()


class Headpiece:  # заставка
    def __init__(self):
        pass

    def start_screen(self, screen):
        fon = pygame.transform.scale(load_image('Fon.jpg'), (WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(fon, (0, 0))
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 30)
        text_coord = 50
        for line in intro_text:
            string_rendered = font.render(line, 1, pygame.Color('white'))
            intro_rect = string_rendered.get_rect()
            text_coord += 10
            intro_rect.top = text_coord
            intro_rect.x = 10
            text_coord += intro_rect.height
            screen.blit(string_rendered, intro_rect)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate()
                elif event.type == pygame.KEYDOWN or \
                        event.type == pygame.MOUSEBUTTONDOWN:
                    return
                pygame.display.flip()
                clock.tick(FPS)


class Labyrinth:  # лабиринт
    def __init__(self, filename, free_tiles, finish_tile):
        self.map = []
        with open(f"{filename}") as input_file:
            for line in input_file:
                self.map.append(list(map(int, line.split())))
        self.height = len(self.map)
        self.width = len(self.map[8])
        self.tile_size = TILE_SIZE
        self.free_tiles = free_tiles
        self.finish_tile = finish_tile

    def render(self, screen):
        colors = {0: (0, 0, 0), 1: (120, 120, 120), 2: (0, 0, 255)}
        for x in range(self.height):
            for y in range(self.width):
                rect = pygame.Rect(y * self.tile_size, x * self.tile_size,
                                   self.tile_size, self.tile_size)
                screen.fill(colors[self.get_tile_id((y, x))], rect)

    def get_tile_id(self, position):
        return self.map[position[1]][position[0]]

    def is_free(self, position):
        return self.get_tile_id(position) in self.free_tiles

    def find_path(self, start, target):
        d = 100
        x, y = start
        distance = [[d] * self.width for _ in range(self.height)]
        distance[y][x] = 0
        prev = [[None] * self.width for _ in range(self.height)]
        queue = [(x, y)]
        while queue:
            x, y = queue.pop(0)
            for dx, dy in (1, 0), (0, 1), (-1, 0), (0, -1):
                next_x, next_y = x + dx, y + dy
                if 0 <= next_x < self.width and 0 < next_y < self.height and \
                        self.is_free((next_x, next_y)) and distance[next_y][next_x] == d:
                    distance[next_y][next_x] = distance[y][x] + 1
                    prev[next_y][next_x] = (x, y)
                    queue.append((next_x, next_y))
        x, y = target
        if distance[y][x] == d or start == target:
            return start
        while prev[y][x] != start:
            x, y = prev[y][x]
        return x, y


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y):
        super().__init__(all_sprites)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = self.frames[self.cur_frame]


class Hero:  # игрок
    def __init__(self, position):
        self.x, self.y = position

    def get_position(self):
        return self.x, self.y

    def set_position(self, position):
        self.x, self.y = position

    def render(self, screen):
        center = self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2
        pygame.draw.circle(screen, (255, 255, 255), center, TILE_SIZE // 2)


class Enemy:  # враг
    def __init__(self, position):
        self.x, self.y = position
        self.delay = 100
        pygame.time.set_timer(ENEMY_EVENT, self.delay)

    def get_position(self):
        return self.x, self.y

    def set_position(self, position):
        self.x, self.y = position

    def render(self, screen):
        center = self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2
        pygame.draw.circle(screen, (255, 0, 0), center, TILE_SIZE // 2)


class Game:
    def __init__(self, labyrinth, hero, enemy):
        self.labyrinth = labyrinth
        self.hero = hero
        self.enemy = enemy

    def render(self, screen):
        self.labyrinth.render(screen)
        self.hero.render(screen)
        self.enemy.render(screen)

    def update_hero(self):
        next_x, next_y = self.hero.get_position()
        if pygame.key.get_pressed()[pygame.K_LEFT]:
            next_x -= 1
        elif pygame.key.get_pressed()[pygame.K_RIGHT]:
            next_x += 1
        elif pygame.key.get_pressed()[pygame.K_UP]:
            next_y -= 1
        elif pygame.key.get_pressed()[pygame.K_DOWN]:
            next_y += 1
        if self.labyrinth.is_free((next_x, next_y)):
            self.hero.set_position((next_x, next_y))

    def move_enemy(self):
        next_pos = self.labyrinth.find_path(self.enemy.get_position(),
                                            self.hero.get_position())
        self.enemy.set_position(next_pos)

    def check_win(self):
        return self.labyrinth.get_tile_id(self.hero.get_position()) == self.labyrinth.finish_tile

    def check_lose(self):
        return self.hero.get_position() == self.enemy.get_position()


def create_particles(position):
    particle_count = 25
    numbers = range(-5, 6)
    for _ in range(particle_count):
        Particle(position, random.choice(numbers), random.choice(numbers))


def show_message(screen, message):
    font = pygame.font.Font(None, 50)
    text = font.render(message, 1, (50, 70, 0))
    text_x = WINDOW_WIDTH // 2 - text.get_width() // 2
    text_y = WINDOW_HEIGHT // 2 - text.get_height() // 2
    text_w = text.get_width()
    text_h = text.get_height()
    pygame.draw.rect(screen, (200, 150, 50), (text_x - 10, text_y - 10,
                                              text_w + 20, text_h + 20))
    screen.blit(text, (text_x, text_y))


def main():
    global count
    global FPS
    pygame.init()
    Headpiece.start_screen(1, screen)

    labyrinth = Labyrinth('Map.txt', [0, 2], 2)
    hero = Hero((13, 11))
    enemy = Enemy((1, 2))
    game = Game(labyrinth, hero, enemy)

    running = True
    game_over = False
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == ENEMY_EVENT and not game_over:
                game.move_enemy()
        if not game_over:
            game.update_hero()
        screen.fill((0, 0, 0))
        game.render(screen)
        if game.check_win():
            game_over = True
            show_message(screen, 'Ты победил!')
            FPS = 50
        if game.check_lose():
            game_over = True
            show_message(screen, 'Поражение...')
            FPS = 50
        if game_over and count < 15:
            count += 1
            x, y = hero.get_position()
            create_particles((x * 32, y * 32))

        all_sprites.draw(screen)
        all_sprites.update()
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == '__main__':
    main()