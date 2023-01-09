import os
import random
from pathlib import Path
from PIL import Image, ImageSequence
from tkinter import messagebox

import pygame
import sys

os.environ['SDL_VIDEO_WINDOW_POS'] = '550, 35'
all_sprites = pygame.sprite.Group()
aliens = pygame.sprite.Group()
player_sprite = pygame.sprite.Group()
player_bullets = pygame.sprite.Group()
aliens_bullets = pygame.sprite.Group()


class GameSettings:
    fps = 60
    screen_size = screen_width, screen_height = 750, 1000


def terminate():
    pygame.quit()
    sys.exit()


def exiting_the_game():
    answer = messagebox.askyesno(title="Подтверждение о выходе", message="Вы хотите выйти из игры?")

    if answer:
        terminate()


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, frames, frame_rate, *groups):
        super().__init__(*groups)
        self.frames = frames
        self.frame_rate = frame_rate
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect()

    def update(self):
        frame_step = GameSettings.fps // self.frame_rate
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
    start_music = FileManager.load_sound('start.mp3')
    start_music.set_volume(0.7)
    start_engine = FileManager.load_sound('start_engine.mp3')
    start_engine.set_volume(0.6)
    space_war = ['Space War']
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()
    start_button = FileManager.load_image('start.png')
    rect = start_button.get_rect()
    rect.x, rect.y = 350, 440

    title_font = pygame.font.SysFont('SPACE MISSION', 65)
    ba_frames = FileManager.load_gif_frames('start.gif')
    background_animation = AnimatedSprite(ba_frames, frame_rate=10)
    start_music.play(-1)

    def to_game():
        start_music.stop()
        start_engine.play()
        pygame.time.wait(5000)

    while True:
        for event in pygame.event.get():
            x, y = pygame.mouse.get_pos()
            if event.type == pygame.QUIT:
                exiting_the_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    to_game()
                    return
                if event.key == pygame.K_ESCAPE:
                    exiting_the_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.mouse.get_pressed()[0]:
                    if rect.collidepoint(x, y):
                        to_game()
                        return

        background_animation.update()
        background_animation.draw(screen)

        margin = 5
        for line in space_war:
            string_rendered = title_font.render(line, True, pygame.Color('DodgerBlue'))
            string_width, string_height = string_rendered.get_size()
            screen.blit(string_rendered, (width // 2 - string_width // 2, margin))

        screen.blit(start_button, rect)
        clock.tick(GameSettings.fps)
        pygame.display.flip()


def game_over(width, height):
    end_music = FileManager.load_sound('game-over.mp3')
    end_music.set_volume(0.7)
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()

    sa_frames = FileManager.load_gif_frames('game_over.gif')
    screen_animation = AnimatedSprite(sa_frames, frame_rate=5)
    end_music.play()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exiting_the_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    exiting_the_game()
                if event.key == pygame.K_ESCAPE:
                    exiting_the_game()

        screen_animation.update()
        screen_animation.draw(screen)
        clock.tick(GameSettings.fps)
        pygame.display.flip()


class FileManager:
    DATA_PATH = Path.cwd() / 'data'

    SPRITES_PATH = DATA_PATH / 'sprites'

    SOUNDS_PATH = DATA_PATH / 'sounds'

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

    @ staticmethod
    def load_sound(name):
        path = FileManager.SOUNDS_PATH / name
        if not path.exists():
            raise FileNotFoundError(f"Файл со звуком '{name}' по пути '{path}' не найден")

        sound = pygame.mixer.Sound(path)
        return sound


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


def spawn_alien(score, bullet_group, *groups):
    if score >= 600:
        SoldierAlien(score, bullet_group, *groups)
    if score >= 500:
        MobileAlien(score, *groups)
    else:
        Alien(score, *groups)


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

        x = random.randrange(GameSettings.screen_width - self.rect.width)
        y = random.randrange(-100, -30)
        self.set_pos(x, y)
        if self.score >= 500:
            self.speed = random.randrange(3, 8)
        else:
            self.speed = random.randrange(1, 6)

    def update(self):
        self.move(*(d * self.speed for d in self.direction))
        if self.rect.top >= GameSettings.screen_height or\
                self.rect.right <= 0 or self.rect.left >= GameSettings.screen_width:
            self.to_start()


class MobileAlien(Alien):
    def to_start(self):
        super().to_start()
        self.direction[0] = random.uniform(-1, 1)


class SoldierAlien(Alien):
    def __init__(self, score, bullet_group, *groups):
        super().__init__(score, *groups)
        self.bullet_group = bullet_group
        self.stop_at = self.size[1] + random.randint(-10, 50)

        self.attack_speed = 0.25
        self.shoot_cooldown = random.randint(0, 60)

    def update(self):
        if self.rect.centery < self.stop_at:
            super().update()
        elif self.shoot_cooldown <= 0:
            self.shoot()
        else:
            self.shoot_cooldown -= 1 * self.attack_speed

    def shoot(self):
        if self.shoot_cooldown <= 0:
            Bullet(self, self.rect.centerx, self.rect.bottom, all_sprites, self.bullet_group, speed=5)
            self.shoot_cooldown = 60


class Bullet(SWSprite):
    image_names = "bullet_player.png", "bullet_alien.png"

    def __init__(self, owner, x: int, y: int, *groups, speed: int = 10):
        image_name = ''
        if isinstance(owner, Player):
            image_name = self.image_names[0]
        elif isinstance(owner, Alien):
            image_name = self.image_names[1]

        super().__init__(image_name, *groups)
        if isinstance(owner, Player):
            self.target = Alien
        elif isinstance(owner, Alien):
            self.target = Player
            self.image = pygame.transform.flip(self.image, False, True)
        else:
            raise ValueError(f'Владелец должен относиться к классу Player или классу Alien')
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = speed

    def update(self):
        self.move(0, self.speed if self.target == Player else -self.speed)
        if self.rect.bottom <= 0 or self.rect.top >= GameSettings.screen_height or \
                self.rect.right <= 0 or self.rect.left >= GameSettings.screen_width:
            self.kill()


class Player(SWSprite):
    image_name = "spaceX.png"

    def __init__(self, *groups, bullet_group, attack_speed: float = 2):
        super().__init__(self.image_name, *groups)
        self.bullet_group = bullet_group

        self.speed = 8
        self.rect.centerx = GameSettings.screen_width / 2
        self.rect.bottom = GameSettings.screen_height - self.speed
        self.attack_speed = attack_speed
        self.shoot_cooldown = 0

    def update(self):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1 * self.attack_speed
        speed = self.speed  # 8 or 5.656854249492381
        keys_pressed = pygame.key.get_pressed()
        if any((keys_pressed[pygame.K_w], keys_pressed[pygame.K_a],
                keys_pressed[pygame.K_s], keys_pressed[pygame.K_d])):
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
            if rect_check.left <= 0 or rect_check.right >= GameSettings.screen_width:
                direction[0] = 0
            if rect_check.top <= 0 or rect_check.bottom >= GameSettings.screen_height:
                direction[1] = 0
            self.move(*(d * speed for d in direction))

    def shoot(self):
        if self.shoot_cooldown <= 0:
            Bullet(self, self.rect.centerx, self.rect.top, all_sprites, self.bullet_group)
            self.shoot_cooldown = 60


def draw_text(screen, score, size, pos):
    font = pygame.font.SysFont('SPACE MISSION', size)
    text = font.render(str(score), True, (0, 255, 0))
    screen.blit(text, pos)


def draw_health(screen, x, y, health):
    heart = FileManager.load_image('live.png')
    rect = heart.get_rect()
    rect.x, rect.y = 5, 6
    green = pygame.Color('green')
    orange = pygame.Color('dark orange')
    red = pygame.Color('red')
    if health < 0:
        health = 0
    width = 200
    height = 15
    health_size = (health / 100) * width
    fill_line = pygame.Rect(x, y, health_size, height)
    fill_outline = pygame.Rect(x, y, width, height)
    if health > 50:
        pygame.draw.rect(screen, green, fill_line)
    elif 20 < health <= 50:
        pygame.draw.rect(screen, orange, fill_line)
    else:
        pygame.draw.rect(screen, red, fill_line)
    pygame.draw.rect(screen, red, fill_outline, 2)
    screen.blit(heart, rect)


def main():
    pygame.init()
    hit_aliens_sound = FileManager.load_sound('strike.mp3')
    hit_aliens_sound.set_volume(0.7)
    fon_music = FileManager.load_sound('fon_sound.mp3')
    damage = FileManager.load_sound('damage.mp3')
    pygame.display.set_caption("Space War")
    clock = pygame.time.Clock()
    start_screen(889, 500)
    screen = pygame.display.set_mode(GameSettings.screen_size)
    pause = False

    score = 0
    health = 100
    player = Player(all_sprites, player_sprite, bullet_group=player_bullets)
    for _ in range(8):
        Alien(score, aliens, all_sprites)
    background_image = FileManager.load_image('screen_fon.png')
    background_rect = background_image.get_rect()

    pause_button = FileManager.load_image('pause.png')
    play_button = FileManager.load_image('play.png')
    play_or_pause = pause_button
    play_or_pause_rect = play_or_pause.get_rect()
    play_or_pause_rect.x, play_or_pause_rect.y = 10, 45

    fon_music.play()
    fon_music.set_volume(0.5)

    while True:
        x, y = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exiting_the_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    exiting_the_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.mouse.get_pressed()[0]:
                    if play_or_pause_rect.collidepoint(x, y):
                        pause = not pause
        if not pause:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exiting_the_game()
                if event.type == pygame.KEYDOWN:
                    player.update()
            if pygame.key.get_pressed()[pygame.K_SPACE]:
                player.shoot()

            all_sprites.update()
            player_bullets_hit_aliens = pygame.sprite.groupcollide(aliens, player_bullets, True, True)
            for _ in player_bullets_hit_aliens:
                score += 10
                spawn_alien(score, aliens_bullets, aliens, all_sprites)
                hit_aliens_sound.play()

            aliens_hit_player = pygame.sprite.groupcollide(player_sprite, aliens, False, True)
            for _ in aliens_hit_player:
                health -= 20
                damage.play()
                spawn_alien(score, aliens_bullets, aliens, all_sprites)
                if health <= 0:
                    fon_music.stop()
                    game_over(889, 500)

            alien_bullets_hit_player = pygame.sprite.groupcollide(player_sprite, aliens_bullets, False, True)
            for _ in alien_bullets_hit_player:
                health -= 10
                damage.play()
                if health <= 0:
                    fon_music.stop()
                    game_over(889, 500)

            play_or_pause = pause_button

            screen.fill('black')
            screen.blit(background_image, background_rect)
            screen.blit(play_or_pause, play_or_pause_rect)
            all_sprites.draw(screen)
            draw_text(screen, "Очки: ", 40, (GameSettings.screen_width * 0.8 - 45, 15))
            draw_text(screen, score, 40, (GameSettings.screen_width * 0.8 + 50, 15))
            draw_health(screen, 20, 20, health)
            clock.tick(GameSettings.fps)
            pygame.display.flip()
        else:
            play_or_pause = play_button
            screen.blit(play_or_pause, play_or_pause_rect)
            pygame.display.flip()


if __name__ == '__main__':
    main()
