import os
import random
from pathlib import Path
from PIL import Image, ImageSequence

import pygame
import sys

FPS = 60
os.environ['SDL_VIDEO_WINDOW_POS'] = '550, 35'
SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = 750, 1000
clock = pygame.time.Clock()
all_sprites = pygame.sprite.Group()
alien = pygame.sprite.Group()
player_sprite = pygame.sprite.Group()
bullets = pygame.sprite.Group()


def terminate():
    pygame.quit()
    sys.exit()


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, frames, frame_rate, *groups):
        super().__init__(*groups)
        self.frames = frames
        self.frame_rate = frame_rate
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect()

    def update(self):
        frame_step = FPS // self.frame_rate
        self.cur_frame += 1
        if self.cur_frame >= len(self.frames) * frame_step:
            self.cur_frame = 0
        self.image = self.frames[self.cur_frame // frame_step]

    def change_frames(self, frames):
        self.frames = frames
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        pos = self.pos
        self.rect = self.image.get_rect()
        self.set_pos(*pos)

    @property
    def pos(self):
        return self.rect.topleft

    @property
    def size(self):
        return self.rect.size

    def move(self, x, y):
        self.rect = self.rect.move(x, y)

    def set_pos(self, x, y):
        self.rect.topleft = x, y

    def draw(self, surface):
        surface.blit(self.image, self.rect)


def start_screen(width, height):
    space_war = ['Space War']
    intro_text = ['Для начала игры нажмите Enter']
    screen = pygame.display.set_mode((width, height))
    title_font = pygame.font.SysFont('SPACE MISSION', 65)
    intro_font = pygame.font.SysFont('SPACE MISSION', 40)
    ba_frames = FileManager.load_gif_frames('start.gif')
    background_animation = AnimatedSprite(ba_frames, frame_rate=10)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return
        background_animation.update()
        background_animation.draw(screen)

        margin = 5
        for line in space_war:
            string_rendered = title_font.render(line, True, pygame.Color('DodgerBlue'))
            string_width, string_height = string_rendered.get_size()
            screen.blit(string_rendered, (width // 2 - string_width // 2, margin))
        for line in intro_text:
            string_rendered = intro_font.render(line, True, pygame.Color('Aqua'))
            string_width, string_height = string_rendered.get_size()
            screen.blit(string_rendered, (width // 2 - string_width // 2, height - string_height - margin))
        clock.tick(FPS)
        pygame.display.flip()


def game_over(width, height):
    screen = pygame.display.set_mode((width, height))
    sa_frames = FileManager.load_gif_frames('game_over.gif')
    screen_animation = AnimatedSprite(sa_frames, frame_rate=5)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                terminate()
        screen_animation.update()
        screen_animation.draw(screen)
        clock.tick(FPS)
        pygame.display.flip()


class FileManager:
    DATA_PATH = Path.cwd() / 'data'

    SPRITES_PATH = DATA_PATH / 'sprites'

    @staticmethod
    def load_image(name, color_key=None):
        path = FileManager.SPRITES_PATH / name
        if not path.exists():
            raise FileNotFoundError(f"Файл с изображением '{name}' по пути '{path}' не найден")

        image = pygame.image.load(path)
        if color_key is not None:
            image = image.convert()
            image.set_colorkey(image.get_at((0, 0)) if color_key == -1 else color_key)
        else:
            image = image.convert_alpha()
        return image

    @staticmethod
    def load_gif_frames(name: str, color_key=None):
        path = FileManager.SPRITES_PATH / name
        if not path.exists():
            raise FileNotFoundError(f"Файл с изображением '{name}' по пути '{path}' не найден")

        gif_image = Image.open(path)
        if gif_image.format != 'GIF' or not gif_image.is_animated:
            raise ValueError(f"Файл '{name}' по пути '{path}' не является анимированным изображением формата GIF")

        frames = []
        for frame in ImageSequence.Iterator(gif_image):
            frame = frame.convert('RGBA')
            pygame_frame = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode)

            if color_key is not None:
                pygame_frame = pygame_frame.convert()
                pygame_frame.set_colorkey(pygame_frame.get_at((0, 0)) if color_key == -1 else color_key)
            else:
                pygame_frame = pygame_frame.convert_alpha()

            frames.append(pygame_frame)
        return frames


class SWSprite(pygame.sprite.Sprite):
    def __init__(self, image_name: str, *groups: pygame.sprite.Group):
        super().__init__(*groups)
        self.image = FileManager.load_image(image_name)
        self.rect = self.image.get_rect()

    def change_image(self, image_name: str):
        self.image = FileManager.load_image(image_name)
        pos = self.pos
        self.rect = self.image.get_rect()
        self.set_pos(*pos)

    @property
    def pos(self):
        return self.rect.topleft

    @property
    def size(self):
        return self.rect.size

    def move(self, x, y):
        self.rect = self.rect.move(x, y)

    def set_pos(self, x, y):
        self.rect.topleft = x, y

    def draw(self, surface):
        surface.blit(self.image, self.rect)


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
        keys_pressed = pygame.key.get_pressed()
        if any((keys_pressed[pygame.K_w], keys_pressed[pygame.K_a], keys_pressed[pygame.K_s], keys_pressed[pygame.K_d])):
            direction = [0, 0]
            if keys_pressed[pygame.K_a]:
                direction[0] = -1
            elif keys_pressed[pygame.K_d]:
                direction[0] = 1
            if keys_pressed[pygame.K_w]:
                direction[1] = -1
            elif keys_pressed[pygame.K_s]:
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
    font = pygame.font.SysFont('SPACE MISSION', size)
    text = font.render(str(score), True, (0, 255, 0))
    screen.blit(text, pos)


def draw_health(screen, x, y, health):
    if health < 0:
        health = 0
    width = 200
    height = 15
    health_size = (health / 100) * width
    fill_line = pygame.Rect(x, y, health_size, height)
    fill_outline = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, pygame.Color('green'), fill_line)
    pygame.draw.rect(screen, pygame.Color('red'), fill_outline, 2)


def main():
    pygame.init()
    pygame.display.set_caption("Space War")
    start_screen(889, 500)
    screen = pygame.display.set_mode(SCREEN_SIZE)
    score = 0
    health = 100
    player = Player(all_sprites, player_sprite)
    for _ in range(8):
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
        for _ in s:
            score += 10
            spawn_alien(score)

        s = pygame.sprite.groupcollide(player_sprite, alien, False, True)
        for _ in s:
            health -= 20
            spawn_alien(score)
            if health == 0:
                game_over(889, 500)

        screen.fill('black')
        all_sprites.draw(screen)
        draw_text(screen, "Очки: ", 40, (SCREEN_WIDTH / 2 - 45, 10))
        draw_text(screen, score, 40, (SCREEN_WIDTH / 2 + 50, 10))
        draw_health(screen, SCREEN_WIDTH - 730, 17, health)
        clock.tick(FPS)
        pygame.display.flip()


if __name__ == '__main__':
    main()
