import os
import random
from pathlib import Path
from PIL import Image

import pygame
import sys

FPS = 60
os.environ['SDL_VIDEO_WINDOW_POS'] = '550, 35'
SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = 750, 1000
BLACK = pygame.Color('black')
clock = pygame.time.Clock()
all_sprites = pygame.sprite.Group()
alien = pygame.sprite.Group()
bullets = pygame.sprite.Group()
start_screen_sprite = pygame.sprite.Group()


def terminate():
    pygame.quit()
    sys.exit()


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, frames):
        super().__init__(start_screen_sprite)
        self.frames = frames
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = pygame.Rect(0, 0, 50, 50)

    def update(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = self.frames[self.cur_frame]


def start_screen(WIDTH, HEIGHT):
    fps = 10
    pygame.font.init()
    space_war = ['Space War']
    intro_text = ['Для начала игры нажмите Enter']
    scr = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Space War")
    font_start = pygame.font.SysFont('SPACE MISSION', 65)
    font_intro = pygame.font.SysFont('SPACE MISSION', 40)
    d = FileManager.load_gif_frames('start.gif')
    AnimatedSprite(d)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return
        start_screen_sprite.update()
        start_screen_sprite.draw(scr)
        for i in space_war:
            string_rendered = font_start.render(i, True, pygame.Color('DodgerBlue'))
            scr.blit(string_rendered, (335, 7))
        for i in intro_text:
            string_rendered = font_intro.render(i, True, pygame.Color('Aqua'))
            scr.blit(string_rendered, (230, 460))
        clock.tick(fps)
        pygame.display.flip()


class FileManager:
    DATA_PATH = Path.cwd() / 'data'

    SPRITES_PATH = DATA_PATH / 'sprites'

    @staticmethod
    def load_image(name, colorkey=None):
        path = FileManager.SPRITES_PATH / name
        if not path.exists():
            raise FileNotFoundError(f"Файл с изображением '{name}' по пути '{path}' не найден")

        image = pygame.image.load(path)
        if colorkey is not None:
            image = image.convert()
            image.set_colorkey(image.get_at((0, 0)) if colorkey == -1 else colorkey)
        else:
            image = image.convert_alpha()
        return image

    @staticmethod
    def load_gif_frames(name: str):
        path = FileManager.SPRITES_PATH / name
        if not path.exists():
            raise FileNotFoundError(f"Файл с изображением '{name}' по пути '{path}' не найден")

        gif_image = Image.open(path)
        if gif_image.format != 'GIF' or not gif_image.is_animated:
            raise ValueError(f"Файл '{name}' по пути '{path}' не является анимированным изображением формата GIF")

        frames = []
        for idx in range(gif_image.n_frames):
            gif_image.seek(idx)
            frame_rgba = gif_image.convert("RGBA")
            pygame_image = pygame.image.fromstring(
                frame_rgba.tobytes(), frame_rgba.size, 'RGBA')
            frames.append(pygame_image)
        return frames


class SWSprite(pygame.sprite.Sprite):
    def __init__(self, image_name: str, *groups: pygame.sprite.Group):
        super().__init__(*groups)
        self.image = FileManager.load_image(image_name)
        self.rect = self.image.get_rect()

    def change_image(self, image_name: str):
        self.image = FileManager.load_image(image_name)
        pos = self.pos()
        self.rect = self.image.get_rect()
        self.set_pos(*pos)

    def pos(self):
        return self.rect.topleft

    def size(self):
        return self.rect.size

    def move(self, x, y):
        self.rect = self.rect.move(x, y)

    def set_pos(self, x, y):
        self.rect.topleft = x, y


def spawn_alien(score):
    if score >= 500:
        MobileAlien(score, all_sprites, alien)
    else:
        Alien(score, all_sprites, alien)


class Alien(SWSprite):
    image_variants = 'alien2.png', 'alien3.png'

    def __init__(self, score, *groups):
        image_name = random.choice(self.image_variants)

        super().__init__(image_name, *groups)
        self.score = score
        self.speed = None
        self.direction = [0.0, 1.0]
        self.to_start()

    def to_start(self):
        image_name = random.choice(self.image_variants)
        self.change_image(image_name)

        x = random.randrange(SCREEN_WIDTH - self.rect.width)
        y = random.randrange(-100, -30)
        self.set_pos(x, y)
        if self.score >= 500:
            self.speed = random.randrange(3, 8)
        else:
            self.speed = random.randrange(1, 6)

    def update(self):
        self.move(*(d * self.speed for d in self.direction))
        if self.rect.top >= SCREEN_HEIGHT or self.rect.right <= 0 or self.rect.left >= SCREEN_WIDTH:
            self.to_start()


class MobileAlien(Alien):
    def to_start(self):
        super().to_start()
        self.direction[0] = random.uniform(-1, 1)


class Bullet(SWSprite):
    image_name = "bullet.png"

    def __init__(self, x, y, *groups):
        super().__init__(self.image_name, *groups)
        self.rect.bottom = y
        self.rect.centerx = x
        self.speed = -10
        self.to_start()

    def to_start(self):
        x = self.rect.centerx - 7
        y = self.rect.bottom
        self.set_pos(x, y)

    def update(self):
        self.move(0, self.speed)
        if self.rect.top >= SCREEN_HEIGHT or self.rect.right <= 0 or self.rect.left >= SCREEN_WIDTH:
            self.kill()


class Player(SWSprite):
    image_name = "spaceX.png"

    def __init__(self, *groups, attack_speed: float = 2):
        super().__init__(self.image_name, *groups)
        self.speed = 8
        self.rect.centerx = SCREEN_WIDTH / 2
        self.rect.bottom = SCREEN_HEIGHT - self.speed
        self.attack_speed = attack_speed
        self.shoot_cooldown = 0

    def update(self):
        if self.shoot_cooldown:
            self.shoot_cooldown -= 1 * self.attack_speed
        speed = self.speed  # 8 or 5.656854249492381
        keystate = pygame.key.get_pressed()
        if any((keystate[pygame.K_w], keystate[pygame.K_a], keystate[pygame.K_s], keystate[pygame.K_d])):
            direction = [0, 0]
            if keystate[pygame.K_a]:
                direction[0] = -1
            elif keystate[pygame.K_d]:
                direction[0] = 1
            if keystate[pygame.K_w]:
                direction[1] = -1
            elif keystate[pygame.K_s]:
                direction[1] = 1

            if all(direction):
                speed = (speed ** 2 / 2) ** 0.5

            rect_check = self.rect.move(*(d * speed for d in direction))
            if rect_check.left <= 0 or rect_check.right >= SCREEN_WIDTH:
                direction[0] = 0
            if rect_check.top <= 0 or rect_check.bottom >= SCREEN_HEIGHT:
                direction[1] = 0
            self.move(*(d * speed for d in direction))

    def shoot(self):
        if self.shoot_cooldown == 0:
            Bullet(self.rect.centerx, self.rect.top, all_sprites, bullets)
            self.shoot_cooldown = 60


def draw_text(screen, score, size, pos):
    pygame.font.init()
    font = pygame.font.SysFont('SPACE MISSION', size)
    text = font.render(str(score), True, (0, 255, 0))
    screen.blit(text, pos)


def main():
    pygame.init()
    start_screen(889, 500)
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("Space War")
    score = 0
    player = Player(all_sprites)
    for i in range(8):
        Alien(score, all_sprites, alien)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN:
                player.update()
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            player.shoot()

        all_sprites.update()
        s = pygame.sprite.groupcollide(alien, bullets, True, True)
        for i in s:
            score += 10
            spawn_alien(score)

        screen.fill(BLACK)
        all_sprites.draw(screen)
        draw_text(screen, "Очки: ", 40, (SCREEN_WIDTH / 2 - 50, 10))
        draw_text(screen, score, 40, (SCREEN_WIDTH / 2 + 50, 10))

        clock.tick(FPS)
        pygame.display.flip()


if __name__ == '__main__':
    main()
