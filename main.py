import os
import random
from typing import Tuple
from tkinter import Tk, messagebox
from operator import itemgetter

import pygame
import sys

from managers import FileManager, SoundManager
from settings import GameSettings
from swsprite import SWSprite

os.environ['SDL_VIDEO_WINDOW_POS'] = '550, 35'


class GameController:
    all_sprites = pygame.sprite.Group()
    aliens = pygame.sprite.Group()
    player_sprite = pygame.sprite.Group()
    player_bullets = pygame.sprite.Group()
    aliens_bullets = pygame.sprite.Group()
    textbox = pygame.sprite.Group()

    score = 0
    player_health = 100
    nickname = ''
    timer = 0

    player = None
    current_boss = None

    @classmethod
    def spawn_alien(cls):
        if cls.current_boss is None:
            if cls.score >= 1000:
                cls.current_boss = BossAlien(cls.aliens_bullets, cls.aliens, cls.all_sprites)
            elif cls.score >= 600:
                SoldierAlien(cls.aliens_bullets, cls.aliens, cls.all_sprites)
            elif cls.score >= 500:
                MobileAlien(cls.aliens, cls.all_sprites)
            else:
                RammingAlien(cls.aliens, cls.all_sprites)

    @classmethod
    def alien_reward(cls, alien):
        if isinstance(alien, BossAlien):
            cls.current_boss = None
            cls.score += 100
        else:
            cls.score += 10

    @classmethod
    def update(cls):
        gs = GameSettings

        cls.all_sprites.update()
        player_bullets_hit_aliens = pygame.sprite.groupcollide(cls.aliens, cls.player_bullets, False, True)
        for alien in player_bullets_hit_aliens:
            alien.health -= 1
            if alien.health <= 0:
                alien.kill()
                cls.alien_reward(alien)
                cls.spawn_alien()
            SoundManager.play_sound('alien_hit', volume=gs.sound_volume)

        aliens_hit_player = pygame.sprite.groupcollide(cls.aliens, cls.player_sprite, False, False)
        for alien in aliens_hit_player:
            alien.health -= 1
            if alien.health <= 0:
                alien.kill()
                cls.spawn_alien()
            cls.player_health -= 20
            SoundManager.play_sound('player_damage', volume=gs.sound_volume)

        alien_bullets_hit_player = pygame.sprite.groupcollide(cls.aliens_bullets, cls.player_sprite, False, True)
        for bullet in alien_bullets_hit_player:
            cls.player_health -= bullet.damage
            SoundManager.play_sound('player_damage', volume=gs.sound_volume)

        if cls.player_health <= 0:
            SoundManager.stop_sound('background_music')
            cls.player.kill()
            cls.player = None
            for a in cls.aliens:
                a.kill()
            game_over(889, 500)

    @classmethod
    def gc_defaults(cls):
        cls.score = 0
        cls.player_health = 100
        cls.timer = 0

        cls.player = Player(cls.all_sprites, cls.player_sprite, bullet_group=cls.player_bullets)
        cls.current_boss = None


def terminate():
    pygame.quit()
    sys.exit()


def exiting_the_game():
    Tk().withdraw()
    answer = messagebox.askyesno(title="Подтверждение о выходе", message="Вы хотите выйти из игры?")

    if answer:
        terminate()


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, frames, *groups, frame_rate: int):
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


class TextInputBox(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(GameController.textbox)
        self.color = pygame.Color('white')
        self.pos = (50, 50)
        self.width = 550
        self.font = pygame.font.SysFont('SPACE MISSION', 100)
        self.cursor = False
        self.text = "Введите ник ..."
        self.render_text()

    def render_text(self):
        if len(self.text) > 11:
            self.text = self.text[:-1]
        text_surf = self.font.render(self.text, True, pygame.Color('DodgerBlue'))
        self.image = pygame.Surface((self.width + 10, text_surf.get_height() + 10))
        self.image.blit(text_surf, (10, 10))
        pygame.draw.rect(self.image, self.color, self.image.get_rect(), 3)
        self.rect = self.image.get_rect(topleft=self.pos)

    def update(self, event_list):
        for event in event_list:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not self.cursor:
                    self.text = ""
                    self.cursor = self.rect.collidepoint(event.pos)
            if event.type == pygame.KEYDOWN:
                if self.cursor:
                    if event.key == pygame.K_RETURN:
                        if len(self.text) == 0 or self.text == "Введите ник":
                            pass
                        else:
                            GameController.nickname = self.text
                            main()
                    elif event.key == pygame.K_BACKSPACE:
                        self.text = self.text[:-1]
                    else:
                        self.text += event.unicode
                    self.render_text()


def input_nick():
    pygame.init()
    screen = pygame.display.set_mode((650, 200))
    pygame.display.set_caption("Space War")
    clock = pygame.time.Clock()
    box = TextInputBox()
    background_image = FileManager.load_image('screen_fon.png')
    background_rect = background_image.get_rect()
    while True:
        event_list = pygame.event.get()
        for event in event_list:
            if event.type == pygame.QUIT:
                exiting_the_game()
        box.update(event_list)
        screen.fill((0, 0, 0))
        screen.blit(background_image, background_rect)
        GameController.textbox.draw(screen)
        clock.tick(GameSettings.fps)
        pygame.display.flip()


def start_screen(width, height):
    gs = GameSettings

    def to_game():
        SoundManager.stop_sound('main_menu_theme')
        SoundManager.play_sound('start_game', volume=gs.music_volume)
        pygame.time.wait(5000)

    start_screen_sprites = pygame.sprite.Group()

    SoundManager.load_sound('main_menu_theme', 'start.mp3')
    SoundManager.load_sound('start_game', 'start_engine.mp3')

    space_war = ['Space War']
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()

    ui_margin = 5

    title_font = pygame.font.SysFont('SPACE MISSION', 65)
    profile = pygame.font.SysFont('SPACE MISSION', 50)
    ba_frames = FileManager.load_gif_frames('start.gif')
    AnimatedSprite(ba_frames, start_screen_sprites, frame_rate=10)

    start_button = UIButton('start.png', start_screen_sprites, text='123456',
                            font=pygame.font.SysFont('SPACE MISSION', 50))
    start_button.rect.centerx = width // 2
    start_button.rect.bottom = height - ui_margin

    icon = UIButton('ikonka.png', start_screen_sprites, text='', font=profile)
    icon.set_pos(ui_margin, ui_margin + 1)

    SoundManager.play_sound('main_menu_theme', volume=gs.music_volume, loop=True)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exiting_the_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return to_game()
                if event.key == pygame.K_ESCAPE:
                    exiting_the_game()
                if event.key == pygame.K_r:
                    result()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    x, y = pygame.mouse.get_pos()
                    if start_button.is_clicked(x, y):
                        return to_game()
                    if icon.is_clicked(x, y):
                        SoundManager.stop_sound('main_menu_theme')
                        input_nick()

        start_screen_sprites.update()
        start_screen_sprites.draw(screen)

        for line in space_war:
            string_rendered = title_font.render(line, True, pygame.Color('DodgerBlue'))
            string_width, string_height = string_rendered.get_size()
            screen.blit(string_rendered, (width // 2 - string_width // 2, ui_margin))

        nickname_rendered = profile.render(GameController.nickname, True, pygame.Color('Tomato'))
        screen.blit(nickname_rendered, (50, ui_margin + 5))

        clock.tick(GameSettings.fps)
        pygame.display.flip()


def game_over(width, height):
    SoundManager.load_sound('game_over', 'game-over.mp3')

    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()

    sa_frames = FileManager.load_gif_frames('game_over.gif')
    screen_animation = AnimatedSprite(sa_frames, frame_rate=5)
    SoundManager.play_sound('game_over', volume=GameSettings.music_volume)

    con = FileManager.load_base('result.db')
    cur = con.cursor()
    result = cur.execute("""SELECT Nickname FROM score
                            WHERE Nickname = ?""", (GameController.nickname,)).fetchall()

    if len(result) == 0:
        entities = (GameController.nickname, GameController.score)
        sql_insert(con, entities)
    else:
        result_score = cur.execute("""SELECT Score FROM score
                                      WHERE Nickname = ?""", (GameController.nickname,)).fetchall()
        old_score = result_score[0][0]
        if old_score < GameController.score:
            entities = (GameController.score, GameController.nickname)
            sql_update(con, entities)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exiting_the_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    GameController.score = 0
                    GameController.player_health = 100
                    main()
                if event.key == pygame.K_ESCAPE:
                    exiting_the_game()

        screen_animation.update()
        screen_animation.draw(screen)
        clock.tick(GameSettings.fps)
        pygame.display.flip()


def sql_insert(con, entities):
    cur = con.cursor()
    cur.execute(
        """INSERT INTO score(Nickname, Score) VALUES(?, ?)""",
        entities)
    con.commit()


def sql_update(con, entities):
    cur = con.cursor()
    cur.execute("""UPDATE score
                   SET Score = ?
                   WHERE Nickname = ?""",
                entities)
    con.commit()


def leader_board(screen, width):
    pygame.font.init()
    i = 35

    title_font_style = pygame.font.SysFont('SPACE MISSION', 60)
    top_font_style = pygame.font.SysFont('SPACE MISSION', 50)
    font_style = pygame.font.SysFont('SPACE MISSION', 50)
    yellow = pygame.Color('yellow')
    red = pygame.Color('red')
    green = pygame.Color('green')

    con = FileManager.load_base('result.db')
    cur = con.cursor()
    result = cur.execute("""SELECT * FROM score
                            ORDER BY Score desc LIMIT 10""").fetchall()

    if len(result) != 0:
        title1 = title_font_style.render('PLAYER', True, yellow)
        title2 = title_font_style.render('SCORE', True, yellow)
        screen.blit(title1, [width / 7 + 20, (700 / 16)])
        screen.blit(title2, [width / 7 + 280, (700 / 16)])
        count = 1
        result.sort(key=itemgetter(1), reverse=True)
        for row in result:
            if count == 1:
                column0 = top_font_style.render(f"{str(count)}.", True, green)
                column1 = top_font_style.render('{:>3}'.format(row[0]), True, green)
                column2 = top_font_style.render('{:30}'.format(row[1]), True, green)
            else:
                column0 = font_style.render(f"{str(count)}.", True, red)
                column1 = font_style.render('{:>3}'.format(row[0]), True, red)
                column2 = font_style.render('{:30}'.format(row[1]), True, red)

            screen.blit(column1, [width / 7 + 30, (700 / 11) + i + 20])
            screen.blit(column2, [width / 5 + 42, (700 / 11) + i + 20])
            screen.blit(column0, [width / 13, (700 / 11) + i + 20])
            count += 1
            i += 55
    else:
        line1_text = title_font_style.render(f"К сожалению,", True, yellow)
        line2_text = title_font_style.render(f"никто ещё не сыграл", True, yellow)
        line3_text = title_font_style.render(f"в игру", True, yellow)

        screen.blit(line1_text, [width / 5 + 30, (700 / 11) + i + 20])
        screen.blit(line2_text, [width / 10 + 17, (700 / 11) + i * 3 + 20])
        screen.blit(line3_text, [width / 3 + 35, (700 / 11) + i * 5 + 20])


def result():
    pygame.display.set_caption('Space war')
    size = width, height = 565, 870
    screen = pygame.display.set_mode(size)
    clock = pygame.time.Clock()
    background = FileManager.load_image("fon_result.png")
    background_rect = background.get_rect()

    while True:
        screen.fill((0, 0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return start_screen(889, 500)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return start_screen(889, 500)
        screen.blit(background, background_rect)
        leader_board(screen, width)
        clock.tick(GameSettings.fps)
        pygame.display.flip()


class UIButton(SWSprite):
    def __init__(self, image: str | pygame.Surface, *groups,
                 text: str, font: pygame.font.Font, color: Tuple[int, int, int] = (0, 0, 0),
                 antialias: bool = True):
        super().__init__(image, *groups)
        self.font = font
        self.text = text
        self.params = (antialias, color)

    def is_clicked(self, x, y):
        return self.rect.collidepoint(x, y)

    def update(self):
        t = self.font.render(self.text, *self.params)
        text_width, text_height = t.get_size()
        text_pos = self.rect.width // 2 - text_width // 2, self.rect.height // 2 - text_height // 2
        self.image.blit(t, text_pos)


class Alien(SWSprite):
    image_variants = 'alien2.png', 'alien3.png'

    def __init__(self, *groups, image_name=None):
        if image_name is None:
            image_name = random.choice(self.image_variants)

        super().__init__(image_name, *groups)

        self.health = 1

        if GameController.score >= 500:
            self.speed = random.randrange(3, 8)
        else:
            self.speed = random.randrange(1, 6)

        self.direction = [0.0, 0.0]
        self.to_start()

    def to_start(self):
        x = random.randrange(GameSettings.screen_width - self.rect.width)
        y = random.randrange(-200, -30)
        self.set_pos(x, y)

    def update(self):
        self.move(*(d * self.speed for d in self.direction))
        if self.rect.top >= GameSettings.screen_height or\
                self.rect.right <= 0 or self.rect.left >= GameSettings.screen_width:
            self.kill()
            GameController.spawn_alien()


class RammingAlien(Alien):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.direction[1] = 1


class MobileAlien(Alien):
    def __init__(self, *groups, image_name=None):
        super().__init__(*groups, image_name=image_name)
        self.direction = [random.uniform(-1, 1), 1]


class SoldierAlien(MobileAlien):
    def __init__(self, bullet_group, *groups, image_name=None):
        super().__init__(*groups, image_name=image_name)
        self.bullet_group = bullet_group

        self.stop_at = self.size[1] + random.randint(-10, 50)

        self.bullet_damage = 10
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
            Bullet(self, self.rect.centerx, self.rect.bottom, GameController.all_sprites, self.bullet_group,
                   damage=10, speed=5)
            self.shoot_cooldown = 60


class BossAlien(SoldierAlien):
    def __init__(self, bullet_group, *groups):
        super().__init__(bullet_group, *groups, image_name='boss.gif')
        self.health = 15

        self.repeat_attack = 3
        self.repeat_cooldown = 0
        self.attack_counter = self.repeat_attack

    def update(self):
        if self.rect.centery < self.stop_at:
            super().update()
        elif self.shoot_cooldown <= 0:
            if self.attack_counter == 0:
                self.attack_counter = self.repeat_attack
            if self.repeat_cooldown <= 0:
                self.shoot()
            else:
                self.repeat_cooldown -= 1 * self.attack_speed
        else:
            self.shoot_cooldown -= 1 * self.attack_speed

    def shoot(self):
        if self.shoot_cooldown <= 0:
            Bullet(self, self.rect.centerx - 50, self.rect.bottom, GameController.all_sprites,
                   self.bullet_group, speed=5)
            Bullet(self, self.rect.centerx + 50, self.rect.bottom, GameController.all_sprites,
                   self.bullet_group, speed=5)
            self.attack_counter -= 1
            if self.attack_counter:
                self.repeat_cooldown = 60 // self.repeat_attack
            else:
                self.shoot_cooldown = 60


class Bullet(SWSprite):
    image_names = "bullet_player.png", "bullet_alien.png"

    def __init__(self, owner, x: int, y: int, *groups, damage: int = 1, speed: int = 10):
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
        self.damage = damage
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
            Bullet(self, self.rect.centerx, self.rect.top, GameController.all_sprites, self.bullet_group)
            self.shoot_cooldown = 60


def draw_text(screen, string, size, pos):
    font = pygame.font.SysFont('SPACE MISSION', size)
    text = font.render(string, True, (0, 255, 0))
    screen.blit(text, pos)


def draw_health(screen, x, y):
    ui_margin = 5

    heart = SWSprite('live.png')
    heart.set_pos(ui_margin, ui_margin)

    width = 200
    height = 15

    h = max(0, GameController.player_health)
    health_size = (h / 100) * width
    fill_line = pygame.Rect(x, y, health_size, height)
    fill_outline = pygame.Rect(x, y, width, height)
    if h > 50:
        pygame.draw.rect(screen, 'green', fill_line)
    elif 20 < h <= 50:
        pygame.draw.rect(screen, 'dark orange', fill_line)
    else:
        pygame.draw.rect(screen, 'red', fill_line)
    pygame.draw.rect(screen, 'red', fill_outline, 2)
    heart.draw(screen)


def main():
    gc = GameController
    gs = GameSettings

    game_ui_sprites = pygame.sprite.Group()

    SoundManager.load_sound('alien_hit', 'strike.mp3')
    SoundManager.load_sound('background_music', 'fon_sound.mp3')
    SoundManager.load_sound('player_damage', 'damage.mp3')

    pygame.display.set_caption("Space War")
    clock = pygame.time.Clock()
    start_screen(889, 500)
    screen = pygame.display.set_mode(gs.screen_size)
    pause = False

    SWSprite('screen_fon.png', gc.all_sprites)

    gc.gc_defaults()
    for _ in range(8):
        RammingAlien(gc.aliens, gc.all_sprites)

    pause_button = FileManager.load_image('pause.png')
    play_button = FileManager.load_image('play.png')
    play_pause_button = UIButton(pause_button, game_ui_sprites, text='PAUSE',
                                 font=pygame.font.SysFont('SPACE MISSION', 40))
    play_pause_button.set_pos(10, 45)

    SoundManager.play_sound('background_music', volume=gs.music_volume, loop=True)

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
                    if play_pause_button.is_clicked(x, y):
                        pause = not pause
        if not pause:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exiting_the_game()
                if event.type == pygame.KEYDOWN:
                    gc.player.update()
            if pygame.key.get_pressed()[pygame.K_SPACE]:
                gc.player.shoot()

            gc.update()

            play_pause_button.change_image(pause_button)
            play_pause_button.text = 'PAUSE'

            screen.fill('black')

            gc.all_sprites.draw(screen)
            draw_text(screen, "Очки: ", 40, (gs.screen_width * 0.8 - 45, 15))
            draw_text(screen, str(gc.score), 40, (gs.screen_width * 0.8 + 50, 15))
            draw_health(screen, 20, 20)
            clock.tick(gs.fps)
        else:
            play_pause_button.change_image(play_button)
            play_pause_button.text = 'PLAY'
        game_ui_sprites.draw(screen)
        game_ui_sprites.update()
        pygame.display.flip()


if __name__ == '__main__':
    input_nick()
