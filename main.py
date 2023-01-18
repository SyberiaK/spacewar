import os
import random
from tkinter import Tk, messagebox
from operator import itemgetter

import pygame
import sys

from draw import draw_coin, draw_health, draw_text
from managers import FileManager, SoundManager
from settings import GameSettings
from sql_funcs import sql_insert, sql_update_score, sql_update_coin
from sprites import AnimatedSprite, SWSprite
from ui import TextInputBox, UIButton

os.environ['SDL_VIDEO_WINDOW_POS'] = '550, 35'


class GameController:
    all_sprites = pygame.sprite.Group()
    aliens = pygame.sprite.Group()
    player_sprite = pygame.sprite.Group()
    player_bullets = pygame.sprite.Group()
    aliens_bullets = pygame.sprite.Group()
    textbox = pygame.sprite.Group()
    coin = pygame.sprite.Group()

    score = 0
    coins = 0
    nickname = ''
    timer = 0
    count = 0
    player_plain = 'spaceX.png'
    pos = [40, 180]
    current_coin = None

    player = None
    current_boss = None

    score_rates = {'ramming': 0, 'mobile': 500, 'soldier': 600, 'elite_soldier': 800, 'boss': 1000}
    aliens_limit = 8

    @classmethod
    def spawn_alien(cls):
        if cls.current_boss is None:
            if cls.score >= cls.score_rates['boss']:
                for alien in cls.aliens:
                    alien.kill()
                cls.current_boss = BossAlien(cls.aliens_bullets, cls.aliens, cls.all_sprites,
                                             player_to_track=cls.player)
            elif cls.score >= cls.score_rates['elite_soldier']:
                EliteSoldierAlien(cls.aliens_bullets, cls.aliens, cls.all_sprites, player_to_track=cls.player)
            elif cls.score >= cls.score_rates['soldier']:
                SoldierAlien(cls.aliens_bullets, cls.aliens, cls.all_sprites)
            elif cls.score >= cls.score_rates['mobile']:
                MobileAlien(cls.aliens, cls.all_sprites)
            else:
                RammingAlien(cls.aliens, cls.all_sprites)
        if cls.current_coin is None and cls.score % 100 == 0:
            cls.current_coin = Coin(cls.coin, cls.all_sprites)

    @classmethod
    def alien_reward(cls, alien):
        if isinstance(alien, BossAlien):
            cls.current_boss = None
            cls.score += 100

            cls.score_rates['mobile'] += 600
            cls.score_rates['soldier'] += 600
            cls.score_rates['elite_soldier'] += 600
            cls.score_rates['boss'] += 600
            for i in range(cls.aliens_limit - 1):
                cls.spawn_alien()
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
            cls.player.health -= 20
            SoundManager.play_sound('player_damage', volume=gs.sound_volume)

        alien_bullets_hit_player = pygame.sprite.groupcollide(cls.aliens_bullets, cls.player_sprite, True, False)
        for bullet in alien_bullets_hit_player:
            cls.player.health -= bullet.damage
            SoundManager.play_sound('player_damage', volume=gs.sound_volume)

        player_get_coin = pygame.sprite.groupcollide(cls.player_sprite, cls.coin, False, True)
        for _ in player_get_coin:
            cls.coins += 1
            cls.current_coin = None

        if cls.player.health <= 0:
            SoundManager.stop_sound('background_music')
            cls.player.kill()
            cls.player = None

            for a in cls.aliens:
                a.kill()
            for b in cls.player_bullets:
                b.kill()
            for c in cls.aliens_bullets:
                c.kill()

            game_over(889, 500)

    @classmethod
    def gc_defaults(cls):
        cls.score = 0
        cls.coins = 0
        cls.timer = 0

        cls.current_coin = None
        cls.player = Player(cls.all_sprites, cls.player_sprite, bullet_group=cls.player_bullets)
        cls.current_boss = None

        cls.score_rates = {'ramming': 0, 'mobile': 500, 'soldier': 600, 'elite_soldier': 800, 'boss': 1000}
        cls.aliens_limit = 8


def terminate():
    pygame.quit()
    sys.exit()


def exiting_the_game():
    Tk().withdraw()
    answer = messagebox.askyesno(title="Подтверждение о выходе", message="Вы хотите выйти из игры?")

    if answer:
        terminate()


def input_nick():
    def on_nick_enter(textbox):
        GameController.nickname = textbox.text
        main()

    screen = pygame.display.set_mode((650, 200))
    pygame.display.set_caption("Space War")
    clock = pygame.time.Clock()
    box = TextInputBox(GameController.textbox, on_enter=on_nick_enter)
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


def shop_screen(screen, event_list):
    d = {'spaceX2': 25, 'spaceX3': 50, 'spaceX4': 100}
    con = FileManager.load_base('result.db')
    cur = con.cursor()
    result_score = cur.execute("""SELECT Coin FROM score
                                      WHERE Nickname = ?""", (GameController.nickname,)).fetchall()
    result_spaceX2 = cur.execute("""SELECT spaceX2 FROM score
                                        WHERE Nickname = ?""", (GameController.nickname,)).fetchall()
    spaceX2 = result_spaceX2[0][0]
    result_spaceX3 = cur.execute("""SELECT spaceX3 FROM score
                                        WHERE Nickname = ?""", (GameController.nickname,)).fetchall()
    spaceX3 = result_spaceX3[0][0]
    result_spaceX4 = cur.execute("""SELECT spaceX4 FROM score
                                        WHERE Nickname = ?""", (GameController.nickname,)).fetchall()
    spaceX4 = result_spaceX4[0][0]

    coin = result_score[0][0]

    def draw_text(string, size, p):
        font = pygame.font.SysFont('SPACE MISSION', size)
        text = font.render(string, True, 'yellow')
        screen.blit(text, p)

    def shop_spaceX():
        GameController.player_plain = 'spaceX.png'
        GameController.pos = [40, 180]

    def shop_spaceX2():
        if spaceX2 == 0:
            if coin - d.get('spaceX2') >= 0:
                cur.execute("""UPDATE score
                               SET spaceX2 = 1
                               WHERE Nickname = ?""", (GameController.nickname,))
                cur.execute("""UPDATE score
                               SET Coin = ?
                               WHERE Nickname = ?""", (coin - d.get('spaceX2'), GameController.nickname,))
                con.commit()
        else:
            GameController.player_plain = 'spaceX2.png'
            GameController.pos = [195, 180]


    def shop_spaceX3():
        if spaceX3 == 0:
            if coin - d.get('spaceX3') >= 0:
                cur.execute("""UPDATE score
                               SET spaceX3 = 1
                               WHERE Nickname = ?""", (GameController.nickname,))
                cur.execute("""UPDATE score
                               SET Coin = ?
                               WHERE Nickname = ?""", (coin - d.get('spaceX3'), GameController.nickname,))
                con.commit()
        else:
            GameController.player_plain = 'spaceX3.png'
            GameController.pos = [360, 180]

    def shop_spaceX4():
        if spaceX4 == 0:
            if coin - d.get('spaceX4') >= 0:
                cur.execute("""UPDATE score
                               SET spaceX4 = 1
                               WHERE Nickname = ?""", (GameController.nickname,))
                cur.execute("""UPDATE score
                               SET Coin = ?
                               WHERE Nickname = ?""", (coin - d.get('spaceX4'), GameController.nickname,))
                con.commit()
        else:
            GameController.player_plain = 'spaceX4.png'
            GameController.pos = [530, 180]

    coin_draw = SWSprite('coin_draw.png')
    coin_draw_count = SWSprite('coin.png')
    ok = SWSprite('ok.png')
    spaceX = FileManager.load_image('spaceX.png')
    spaceX_rect = spaceX.get_rect()
    spaceX_rect.x, spaceX_rect.y = 10, 50
    spaceX2_im = FileManager.load_image('spaceX2_shop.png')
    spaceX2_rect = spaceX2_im.get_rect()
    spaceX2_rect.x, spaceX2_rect.y = 125, 5
    spaceX3_im = FileManager.load_image('spaceX3_shop.png')
    spaceX3_rect = spaceX3_im.get_rect()
    spaceX3_rect.x, spaceX3_rect.y = 295, 5
    spaceX4_im = FileManager.load_image('spaceX4_shop.png')
    spaceX4_rect = spaceX4_im.get_rect()
    spaceX4_rect.x, spaceX4_rect.y = 468, 5
    screen.blit(spaceX, [10, 50])
    screen.blit(spaceX2_im, [125, 5])
    screen.blit(spaceX3_im, [295, 5])
    screen.blit(spaceX4_im, [468, 5])
    coin_draw_count.set_pos(10, 305)
    coin_draw_count.draw(screen)
    draw_text(': ', 50, (58, 310))
    draw_text(str(coin), 45, (78, 315))
    ok.set_pos(*GameController.pos)
    ok.draw(screen)
    if spaceX2 == 0:
        coin_draw.set_pos(170, 180)
        coin_draw.draw(screen)
        draw_text(': 25', 40, (210, 185))
    if spaceX3 == 0:
        coin_draw.set_pos(330, 180)
        coin_draw.draw(screen)
        draw_text(': 50', 40, (370, 185))
    if spaceX4 == 0:
        coin_draw.set_pos(487, 180)
        coin_draw.draw(screen)
        draw_text(': 100', 40, (527, 185))
    for event in event_list:
        x, y = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if spaceX_rect.collidepoint(x, y):
                shop_spaceX()
            elif spaceX2_rect.collidepoint(x, y):
                shop_spaceX2()
            elif spaceX3_rect.collidepoint(x, y):
                shop_spaceX3()
            elif spaceX4_rect.collidepoint(x, y):
                shop_spaceX4()


def shop():
    screen = pygame.display.set_mode((640, 360))
    pygame.display.set_caption("Space War")
    clock = pygame.time.Clock()
    background_image = FileManager.load_image('fon_shop.png')
    background_rect = background_image.get_rect()
    while True:
        event_list = pygame.event.get()
        for event in event_list:
            if event.type == pygame.QUIT:
                exiting_the_game()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    return start_screen(889, 500)
        screen.fill((0, 0, 0))
        screen.blit(background_image, background_rect)
        shop_screen(screen, event_list)
        clock.tick(GameSettings.fps)
        pygame.display.flip()


def start_screen(width, height):
    gc, gs = GameController, GameSettings

    def to_game():
        SoundManager.stop_sound('main_menu_theme')
        SoundManager.play_sound('start_game', volume=gs.music_volume)
        pygame.time.wait(5000)

    def draw_coin_on_start_screen():
        con = FileManager.load_base('result.db')
        cur = con.cursor()
        result_coin = cur.execute("""SELECT Coin FROM score
                                     WHERE Nickname = ?""", (gc.nickname,)).fetchall()
        if len(result_coin) == 0:
            entities = (gc.nickname, '0', '0', '0', '0', '0')
            sql_insert(con, entities)
            old_coin = 0
        else:
            old_coin = result_coin[0][0]
        coin_draw = SWSprite('coin_draw.png')
        coin_draw.set_pos(769, 10)

        draw_text(screen, ': ', 45, (811, 13))
        draw_text(screen, str(old_coin), 45, (839, 15))
        coin_draw.draw(screen)

    start_screen_sprites = pygame.sprite.Group()

    space_war = ['Space War']
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()

    ui_margin = 5

    title_font = pygame.font.SysFont('SPACE MISSION', 65)
    profile = pygame.font.SysFont('SPACE MISSION', 50)
    ba_frames = FileManager.load_gif_frames('start.gif')
    AnimatedSprite(ba_frames, start_screen_sprites, frame_rate=10, update_rate=gs.fps)

    start_button = UIButton('red_btn.png', start_screen_sprites, text='START',
                            font=profile)
    start_button.rect.centerx = width // 2
    start_button.rect.bottom = height - ui_margin

    shop_button = UIButton('yellow_btn.png', start_screen_sprites, text='SHOP',
                            font=pygame.font.SysFont('SPACE MISSION', 50))
    shop_button.rect.centerx = width - 100
    shop_button.rect.bottom = height - ui_margin

    resultat_button = UIButton('green_btn.png', start_screen_sprites, text='SCORE',
                               font=pygame.font.SysFont('SPACE MISSION', 50))
    resultat_button.rect.centerx = 100
    resultat_button.rect.bottom = height - ui_margin

    icon = UIButton('ikonka.png', start_screen_sprites, text='', font=profile)
    icon.set_pos(ui_margin, ui_margin + 1)

    if 'main_menu_theme' not in SoundManager.playing_loops:
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
                    return result_screen()
                if event.key == pygame.K_m:
                    return shop()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pos = pygame.mouse.get_pos()
                    if start_button.is_clicked(*pos):
                        return to_game()
                    if shop_button.is_clicked(*pos):
                        return shop()
                    if resultat_button.is_clicked(*pos):
                        return result_screen()
                    if icon.is_clicked(*pos):
                        SoundManager.stop_sound('main_menu_theme')
                        return input_nick()

        start_screen_sprites.update()
        start_screen_sprites.draw(screen)

        for line in space_war:
            string_rendered = title_font.render(line, True, pygame.Color('DodgerBlue'))
            string_width, string_height = string_rendered.get_size()
            screen.blit(string_rendered, (width // 2 - string_width // 2, ui_margin))

        nickname_rendered = profile.render(gc.nickname, True, pygame.Color('Tomato'))
        screen.blit(nickname_rendered, (50, ui_margin + 5))
        draw_coin_on_start_screen()

        clock.tick(gs.fps)
        pygame.display.flip()


def game_over(width, height):
    gc, gs = GameController, GameSettings

    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()
    end_screen_sprites = pygame.sprite.Group()

    sa_frames = FileManager.load_gif_frames('game_over.gif')
    AnimatedSprite(sa_frames, end_screen_sprites, frame_rate=5, update_rate=gs.fps)
    SoundManager.play_sound('game_over', volume=gs.music_volume)

    end_button = UIButton('red_btn.png', end_screen_sprites, text='RETURN',
                            font=pygame.font.SysFont('SPACE MISSION', 50))
    end_button.rect.centerx = width // 2
    end_button.rect.bottom = height - 10

    con = FileManager.load_base('result.db')
    cur = con.cursor()

    result_score = cur.execute("""SELECT Score FROM score
                                  WHERE Nickname = ?""", (GameController.nickname,)).fetchall()
    result_coin = cur.execute("""SELECT Coin FROM score
                                  WHERE Nickname = ?""", (GameController.nickname,)).fetchall()

    old_score = result_score[0][0]
    old_coin = result_coin[0][0]
    if old_score < gc.score:
        entities = (gc.score, gc.nickname)
        sql_update_score(con, entities)
    entities = (gc.coins + old_coin, gc.nickname)
    sql_update_coin(con, entities)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exiting_the_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    main()
                if event.key == pygame.K_ESCAPE:
                    exiting_the_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    x, y = pygame.mouse.get_pos()
                    if end_button.is_clicked(x, y):
                        return main()

        end_screen_sprites.update()
        end_screen_sprites.draw(screen)
        clock.tick(GameSettings.fps)
        pygame.display.flip()


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


def result_screen():
    size = width, height = 565, 870
    screen = pygame.display.set_mode(size)
    clock = pygame.time.Clock()
    background = FileManager.load_image("fon_result.png")
    background_rect = background.get_rect()

    while True:
        screen.fill((0, 0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exiting_the_game()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    return start_screen(889, 500)
        screen.blit(background, background_rect)
        leader_board(screen, width)
        clock.tick(GameSettings.fps)
        pygame.display.flip()


class Alien(SWSprite):
    health = 1
    image_variants = 'alien2.png', 'alien3.png'

    def __init__(self, *groups, image_name=None):
        if image_name is None:
            image_name = random.choice(self.image_variants)

        super().__init__(image_name, *groups)

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
        if self.rect.centery < self.stop_at or type(self) is not SoldierAlien:
            super().update()
        elif self.shoot_cooldown <= 0:
            self.shoot()
        else:
            self.shoot_cooldown -= 1 * self.attack_speed

    def shoot(self):
        if self.shoot_cooldown <= 0:
            Bullet(self, self.rect.centerx, self.rect.bottom, GameController.all_sprites, self.bullet_group,
                   damage=self.bullet_damage, speed=5)
            self.shoot_cooldown = 60


class EliteSoldierAlien(SoldierAlien):
    def __init__(self, bullet_group, *groups, player_to_track, image_name=None):
        super().__init__(bullet_group, *groups, image_name=image_name)
        self.attack_speed = 0.5

        self.move_to_x = None
        self.player_to_track = player_to_track

    def update(self):
        if self.rect.centery < self.stop_at or type(self) is not EliteSoldierAlien:
            super().update()
        else:
            self.direction[1] = 0
            if self.shoot_cooldown <= 0:
                self.shoot()
            else:
                if self.shoot_cooldown > 10:
                    self.follow_player()
                self.shoot_cooldown -= 1 * self.attack_speed

    def follow_player(self):
        alien_x = self.rect.centerx
        player_x = self.player_to_track.rect.centerx
        if self.move_to_x is None or abs(alien_x - self.move_to_x) > 5:
            self.move_to_x = player_x
            self.direction[0] = 0.5 if alien_x < player_x else -0.5
        else:
            self.move_to_x = None
            self.direction[0] = 0
        super().update()


class BossAlien(EliteSoldierAlien):
    health = 45

    def __init__(self, bullet_group, *groups, player_to_track):
        super().__init__(bullet_group, *groups, player_to_track=player_to_track, image_name='boss.gif')
        self.speed = 8

        self.repeat_attack = 3
        self.repeat_cooldown = 0
        self.attack_counter = self.repeat_attack

        self.spawn_ram_cooldown = 0
        self.spawn_soldier_cooldown = 0

        self.stage_map = {45: 1, 30: 2, 15: 3}
        self.current_stage = 1

    def update(self):
        if self.stage_map.get(self.health, None) is not None:
            new_stage = self.stage_map[self.health]
            if self.current_stage != new_stage:
                self.current_stage = new_stage
        if self.rect.centery < self.stop_at:
            super().update()
        else:
            self.direction[1] = 0
            match self.current_stage:
                case 1: self.first_stage()
                case 2: self.second_stage()
                case 3: self.third_stage()

    def first_stage(self):
        if self.shoot_cooldown <= 0:
            if self.attack_counter == 0:
                self.attack_counter = self.repeat_attack
            if self.repeat_cooldown <= 0:
                self.shoot()
            else:
                self.repeat_cooldown -= 1 * self.attack_speed
        else:
            if self.shoot_cooldown > 10:
                self.follow_player()
            self.shoot_cooldown -= 1 * self.attack_speed

    def second_stage(self):
        if abs(self.rect.centerx - (center_x := GameSettings.screen_width // 2)) > 10:
            self.direction[0] = 0.5 if self.rect.centerx < center_x else -0.5
            super().update()
        elif self.spawn_ram_cooldown <= 0:
            self.spawn_ram()
        else:
            self.spawn_ram_cooldown -= 1 * self.attack_speed

    def third_stage(self):
        self.first_stage()

        if self.spawn_ram_cooldown <= 0:
            self.spawn_ram()
        else:
            self.spawn_ram_cooldown -= 1 * self.attack_speed

        if self.spawn_soldier_cooldown <= 0:
            self.spawn_soldier()
        else:
            self.spawn_soldier_cooldown -= 1 * self.attack_speed

    def shoot(self):
        if self.shoot_cooldown <= 0:
            Bullet(self, self.rect.centerx - 50, self.rect.bottom, GameController.all_sprites,
                   self.bullet_group, damage=self.bullet_damage, speed=5)
            Bullet(self, self.rect.centerx + 50, self.rect.bottom, GameController.all_sprites,
                   self.bullet_group, damage=self.bullet_damage, speed=5)
            self.attack_counter -= 1
            if self.attack_counter:
                self.repeat_cooldown = 60 // self.repeat_attack
            else:
                self.shoot_cooldown = 60

    def spawn_ram(self):
        gc = GameController
        if self.spawn_ram_cooldown <= 0:
            player_x = self.player_to_track.pos[0]
            for i in range(-1, 2):
                r = RammingAlien(gc.aliens, gc.all_sprites)
                r.health = 2
                if GameController.player_plain == "spaceX4.png" or GameController.player_plain == "spaceX3.png":
                    r.speed = 15
                else:
                    r.speed = 10
                r.set_pos(player_x + 50 * i, -100 + random.uniform(-30, 30))
            self.spawn_ram_cooldown = 120

    def spawn_soldier(self):
        gc = GameController
        if self.spawn_soldier_cooldown <= 0:
            player_x = self.player_to_track.pos[0]
            r = SoldierAlien(gc.aliens_bullets, gc.aliens, gc.all_sprites)
            r.set_pos(player_x, r.pos[1])
            self.spawn_soldier_cooldown = 240


class Coin(Alien):
    def __init__(self, *groups):
        super().__init__(*groups, image_name='coin.png')
        self.speed = 3
        self.direction[1] = 1


class Bullet(SWSprite):
    image_names = "bullet_player.png", "bullet_alien.png", "bullet_boss.png"

    def __init__(self, owner, x: int, y: int, *groups, damage: int = 1, speed: int = 10):
        image_name = ''
        if isinstance(owner, Player):
            image_name = self.image_names[0]
        elif isinstance(owner, BossAlien):
            image_name = self.image_names[2]
        elif isinstance(owner, Alien):
            image_name = self.image_names[1]

        super().__init__(image_name, *groups)
        if isinstance(owner, Player):
            self.target = Alien
        elif isinstance(owner, BossAlien):
            self.target = Player
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
    health = 100
    image_names = "spaceX.png", "spaceX2.png", "spaceX3.png", "spaceX4.png"

    def __init__(self, *groups, bullet_group, attack_speed: float = 2):
        image_name = ''
        if GameController.player_plain == 'spaceX.png':
            image_name = self.image_names[0]
        elif GameController.player_plain == 'spaceX2.png':
            image_name = self.image_names[1]
        elif GameController.player_plain == 'spaceX3.png':
            image_name = self.image_names[2]
        elif GameController.player_plain == 'spaceX4.png':
            image_name = self.image_names[3]

        super().__init__(image_name, *groups)
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
            if GameController.player_plain == 'spaceX.png':
                Bullet(self, self.rect.centerx, self.rect.top, GameController.all_sprites, self.bullet_group)
            elif GameController.player_plain == 'spaceX2.png':
                Bullet(self, self.rect.centerx - 5, self.rect.top, GameController.all_sprites, self.bullet_group)
                Bullet(self, self.rect.centerx + 5, self.rect.top, GameController.all_sprites, self.bullet_group)
            elif GameController.player_plain == 'spaceX3.png':
                Bullet(self, self.rect.centerx - 30, self.rect.centery + 5, GameController.all_sprites,
                       self.bullet_group)
                Bullet(self, self.rect.centerx + 30, self.rect.centery + 5, GameController.all_sprites,
                       self.bullet_group)
                Bullet(self, self.rect.centerx, self.rect.top, GameController.all_sprites, self.bullet_group)
            elif GameController.player_plain == 'spaceX4.png':
                Bullet(self, self.rect.centerx, self.rect.top, GameController.all_sprites, self.bullet_group)
                Bullet(self, self.rect.centerx - 30, self.rect.centery + 15, GameController.all_sprites,
                       self.bullet_group)
                Bullet(self, self.rect.centerx + 30, self.rect.centery + 15, GameController.all_sprites,
                       self.bullet_group)
                Bullet(self, self.rect.centerx - 45, self.rect.centery + 30, GameController.all_sprites,
                       self.bullet_group)
                Bullet(self, self.rect.centerx + 45, self.rect.centery + 30, GameController.all_sprites,
                       self.bullet_group)
            self.shoot_cooldown = 60


def main():
    gc = GameController
    gs = GameSettings

    game_ui_sprites = pygame.sprite.Group()

    pygame.display.set_caption("Space War")
    clock = pygame.time.Clock()
    start_screen(889, 500)
    screen = pygame.display.set_mode(gs.screen_size)
    pause = False

    SWSprite('screen_fon.png', gc.all_sprites)

    gc.gc_defaults()
    for _ in range(gc.aliens_limit):
        RammingAlien(gc.aliens, gc.all_sprites)

    pause_button = FileManager.load_image('yellow_btn.png')
    play_button = FileManager.load_image('green_btn.png', 'white')
    play_pause_button = UIButton(pause_button, game_ui_sprites, text='PAUSE',
                                 font=pygame.font.SysFont('SPACE MISSION', 40))
    play_pause_button.set_pos(10, 75)

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
            draw_health(screen, gc.player, 20, 50, 200, 15)
            draw_coin(screen, gc.coins)
            if gc.current_boss:
                draw_health(screen, gc.current_boss, gs.screen_width // 2 - 200, 20, 400, 15)
            clock.tick(gs.fps)
        else:
            play_pause_button.change_image(play_button)
            play_pause_button.text = 'PLAY'
        game_ui_sprites.draw(screen)
        game_ui_sprites.update()
        pygame.display.flip()


if __name__ == '__main__':
    pygame.init()

    SoundManager.load_sound('main_menu_theme', 'start.mp3')
    SoundManager.load_sound('start_game', 'start_engine.mp3')

    SoundManager.load_sound('alien_hit', 'strike.mp3')
    SoundManager.load_sound('background_music', 'fon_sound.mp3')
    SoundManager.load_sound('player_damage', 'damage.mp3')

    SoundManager.load_sound('game_over', 'game-over.mp3')

    input_nick()
