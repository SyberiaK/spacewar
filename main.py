import math
import os
import random
from tkinter import Tk, messagebox

import pygame
import sys

from draw import draw_coin, draw_health, draw_text
from managers import FileManager, SoundManager
from settings import GameSettings
from sql_funcs import sql_insert, sql_update_score, sql_update_coin
from sprites import AnimatedSprite, SWSprite
from ui import TextInputBox, UIButton

os.environ['SDL_VIDEO_WINDOW_POS'] = '550, 35'

"Класс, контролирующий игру: спавн пришельцов и монет, соприкосновения, отправка на экран смерти"


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
        if cls.current_coin in [None, 'deleted'] and cls.score % 100 == 0:
            cls.current_coin = Coin(cls.coin, cls.all_sprites)

    @classmethod
    def alien_reward(cls, alien):
        if isinstance(alien, BossAlien):
            cls.current_boss = None
            cls.score += 100
            cls.coins += 5

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

        if isinstance(cls.current_coin, Coin) and cls.current_coin.pos[1] > gs.screen_height:
            cls.current_coin.kill()
            cls.current_coin = 'deleted'

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


"Выход из игры"


def terminate():
    pygame.quit()
    sys.exit()


"Подтверждение о выходе"


def exiting_the_game():
    Tk().withdraw()
    answer = messagebox.askyesno(title="Подтверждение о выходе", message="Вы хотите выйти из игры?")

    if answer:
        terminate()


"Запуск класса ввода ника"


def input_nick():
    nick_entered = False

    def on_nick_enter(textbox):
        nonlocal nick_entered

        GameController.nickname = textbox.text
        nick_entered = True

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
        if nick_entered:
            return
        box.update(event_list)
        screen.fill((0, 0, 0))
        screen.blit(background_image, background_rect)
        GameController.textbox.draw(screen)
        clock.tick(GameSettings.fps)
        pygame.display.flip()


"Экран магазина: отрисовка монет, покупка кораблей, проверка на количество монет, обновление базы данных," \
"отрисовка выбора корабля"


def shop_screen(screen, event_list):
    d = {'spaceX2': 25, 'spaceX3': 50, 'spaceX4': 100}
    con = FileManager.load_base('result.db')
    cur = con.cursor()
    result_score = cur.execute("""SELECT Coin FROM score
                                      WHERE Nickname = ?""", (GameController.nickname,)).fetchall()
    result_space_x2 = cur.execute("""SELECT spaceX2 FROM score
                                        WHERE Nickname = ?""", (GameController.nickname,)).fetchall()
    space_x2 = result_space_x2[0][0]
    result_space_x3 = cur.execute("""SELECT spaceX3 FROM score
                                        WHERE Nickname = ?""", (GameController.nickname,)).fetchall()
    space_x3 = result_space_x3[0][0]
    result_space_x4 = cur.execute("""SELECT spaceX4 FROM score
                                        WHERE Nickname = ?""", (GameController.nickname,)).fetchall()
    space_x4 = result_space_x4[0][0]

    coin = result_score[0][0]

    def _draw_text(string, size, p):
        font = pygame.font.SysFont('SPACE MISSION', size)
        text = font.render(string, True, 'yellow')
        screen.blit(text, p)

    def shop_space_x():
        GameController.player_plain = 'spaceX.png'
        GameController.pos = [40, 180]

    def shop_space_x2():
        if space_x2 == 0:
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

    def shop_space_x3():
        if space_x3 == 0:
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

    def shop_space_x4():
        if space_x4 == 0:
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

    shop_ui = pygame.sprite.Group()

    coin_draw_count = SWSprite('coin.png', shop_ui)
    coin_draw_count.set_pos(10, 305)

    ok = SWSprite('ok.png', shop_ui)
    ok.set_pos(*GameController.pos)

    space_x_spr = SWSprite('spaceX.png', shop_ui)
    space_x_spr.set_pos(10, 50)
    space_x2_spr = SWSprite('spaceX2_shop.png', shop_ui)
    space_x2_spr.set_pos(125, 5)
    space_x3_spr = SWSprite('spaceX3_shop.png', shop_ui)
    space_x3_spr.set_pos(295, 5)
    space_x4_spr = SWSprite('spaceX4_shop.png', shop_ui)
    space_x4_spr.set_pos(468, 5)

    if space_x2 == 0:
        SWSprite('coin_draw.png', shop_ui).set_pos(170, 180)
        _draw_text(': 25', 40, (210, 185))
    if space_x3 == 0:
        SWSprite('coin_draw.png', shop_ui).set_pos(330, 180)
        _draw_text(': 50', 40, (370, 185))
    if space_x4 == 0:
        SWSprite('coin_draw.png', shop_ui).set_pos(487, 180)
        _draw_text(': 100', 40, (527, 185))

    _draw_text(': ', 50, (58, 310))
    _draw_text(str(coin), 45, (78, 315))
    shop_ui.draw(screen)
    shop_ui.update()

    for event in event_list:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                pos = pygame.mouse.get_pos()
                if space_x_spr.rect.collidepoint(*pos):
                    shop_space_x()
                elif space_x2_spr.rect.collidepoint(*pos):
                    shop_space_x2()
                elif space_x3_spr.rect.collidepoint(*pos):
                    shop_space_x3()
                elif space_x4_spr.rect.collidepoint(*pos):
                    shop_space_x4()


"Запуск функции магазина, установка фона и кнопки"


def shop():
    ui_margin = 5

    screen = pygame.display.set_mode((640, 360))
    pygame.display.set_caption("Space War")
    clock = pygame.time.Clock()
    shop_screen_sprites = pygame.sprite.Group()
    background_image = FileManager.load_image('fon_shop.png')
    background_rect = background_image.get_rect()

    donat_button = UIButton('green_btn.png', shop_screen_sprites, text='DONATE',
                            font=pygame.font.SysFont('SPACE MISSION', 50))
    donat_button.rect.centerx = 640 - 100
    donat_button.rect.bottom = 360 - ui_margin

    while True:
        event_list = pygame.event.get()
        for event in event_list:
            if event.type == pygame.QUIT:
                exiting_the_game()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pos = pygame.mouse.get_pos()
                    if donat_button.is_clicked(*pos):
                        return donat()

        screen.fill((0, 0, 0))
        screen.blit(background_image, background_rect)
        shop_screen(screen, event_list)
        shop_screen_sprites.update()
        shop_screen_sprites.draw(screen)

        clock.tick(GameSettings.fps)
        pygame.display.flip()


"Экран доната"


def donat_screen(screen):
    def draw_text_d(string, size, p):
        font = pygame.font.SysFont('SPACE MISSION', size)
        text = font.render(string, True, 'green')
        screen.blit(text, p)

    draw_text_d('Положи мамину карту', 70, (65, 40))
    draw_text_d('на место', 70, (220, 100))
    draw_text_d('И больше так не делай!', 70, (50, 300))


"Функция доната"


def donat():
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
                if event.key == pygame.K_BACKSPACE:
                    return shop()

        screen.fill((0, 0, 0))
        screen.blit(background_image, background_rect)
        donat_screen(screen)
        clock.tick(GameSettings.fps)
        pygame.display.flip()


"Стартовый экран: запуск музыкальных эффектов, кнопки в другие функции, запись в базу данных, установка" \
"на фон GIF, отрисовка разного рода информации"


def start_screen(width, height):
    gc, gs = GameController, GameSettings

    def to_game():
        SoundManager.stop_sound('main_menu_theme')
        SoundManager.play_sound('start_game', volume=gs.music_volume)

        timer_font = pygame.font.SysFont('SPACE MISSION', 100)

        start_button.kill()
        shop_button.kill()
        resultat_button.kill()
        icon.kill()

        start_ticks = pygame.time.get_ticks()
        while True:
            for _event in pygame.event.get():
                if _event.type == pygame.QUIT:
                    exiting_the_game()
                if _event.type == pygame.KEYDOWN:
                    if _event.key == pygame.K_ESCAPE:
                        exiting_the_game()
            start_timer = math.ceil(5 - ((pygame.time.get_ticks() - start_ticks) / 1000))
            if start_timer <= 0:
                main()
                break

            start_screen_sprites.update()
            start_screen_sprites.draw(screen)

            timer_rendered = timer_font.render(str(start_timer), True, pygame.Color('DodgerBlue'))
            timer_rendered_outline = timer_font.render(str(start_timer), True, pygame.Color('white'))
            _string_width, _string_height = timer_rendered.get_size()
            timer_pos = width // 2 - _string_width // 2, height // 2 - _string_height // 2
            for x in range(-2, 3, 4):
                for y in range(-2, 3, 4):
                    _pos = timer_pos[0] + x, timer_pos[1] + y
                    screen.blit(timer_rendered_outline, _pos)
            screen.blit(timer_rendered, timer_pos)

            clock.tick(gs.fps)
            pygame.display.flip()

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
                    to_game()
                if event.key == pygame.K_ESCAPE:
                    exiting_the_game()
                if event.key == pygame.K_r:
                    result_screen()
                if event.key == pygame.K_m:
                    shop()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pos = pygame.mouse.get_pos()
                    if start_button.is_clicked(*pos):
                        to_game()
                    if shop_button.is_clicked(*pos):
                        shop()
                        screen = pygame.display.set_mode((width, height))
                    if resultat_button.is_clicked(*pos):
                        result_screen()
                        screen = pygame.display.set_mode((width, height))
                    if icon.is_clicked(*pos):
                        input_nick()
                        screen = pygame.display.set_mode((width, height))

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


"Экран смерти: обновление базы данных, музыкальный эффект, установка" \
"на фон GIF, отрисовка разного рода информации, кнопка на стартовый кран"


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
                    return start_screen(889, 500)
                if event.key == pygame.K_ESCAPE:
                    exiting_the_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    x, y = pygame.mouse.get_pos()
                    if end_button.is_clicked(x, y):
                        return start_screen(889, 500)

        end_screen_sprites.update()
        end_screen_sprites.draw(screen)
        clock.tick(GameSettings.fps)
        pygame.display.flip()


"Экран результатов: отрисовка таблицы результатов"


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
        result.sort(key=lambda x: x[1], reverse=True)
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


"Функция запускает экран результатов"


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
                    return
        screen.blit(background, background_rect)
        leader_board(screen, width)
        clock.tick(GameSettings.fps)
        pygame.display.flip()


"Начальный класс для движения обычных пришельцев, определение разных скоростей"


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
        if self.rect.top >= GameSettings.screen_height or \
                self.rect.right <= 0 or self.rect.left >= GameSettings.screen_width:
            self.kill()
            GameController.spawn_alien()


"Класс, для обычных прищельцов, двигающихся по y"


class RammingAlien(Alien):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.direction[1] = 1


"Класс, для обычных прищельцов, двигающихся по x и y"


class MobileAlien(Alien):
    def __init__(self, *groups, image_name=None):
        super().__init__(*groups, image_name=image_name)
        self.direction = [random.uniform(-1, 1), 1]


"Класс, для прищельцов, которые останавливаются и стреляют в игрока"


class SoldierAlien(MobileAlien):
    def __init__(self, bullet_group, *groups, image_name=None):
        super().__init__(*groups, image_name=image_name)
        self.bullet_group = bullet_group

        self.stop_at = self.size[1] + random.randint(-10, 50)

        self.bullet_damage = 10
        self.attack_speed = 0.25
        self.shoot_cooldown = random.randint(0, 60)

    def update(self):
        if self.rect.left < 0:
            self.direction[0] = 1
        elif self.rect.right > GameSettings.screen_width:
            self.direction[0] = -1
        elif type(self) is SoldierAlien:
            self.direction[0] = 0
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


"Класс, для прищельцов, которые двигаются по x за игроком и стреляют в него"


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

    "Движение за игроком"

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


"Класс, для босса, стреляющего в игрока"


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
                case 1:
                    self.first_stage()
                case 2:
                    self.second_stage()
                case 3:
                    self.third_stage()

    "Первая атака босса: движение за игроком и стрельба в него"

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

    "Вторая атака босса: остановка босса по центру и направление атаки тарана"

    def second_stage(self):
        if abs(self.rect.centerx - (center_x := GameSettings.screen_width // 2)) > 10:
            self.direction[0] = 0.5 if self.rect.centerx < center_x else -0.5
            super().update()
        elif self.spawn_ram_cooldown <= 0:
            self.spawn_ram()
        else:
            self.spawn_ram_cooldown -= 1 * self.attack_speed

    "Третья атака босса: следование за игроком и стрельба в него, направление атаки тарана и спавн стреляющих" \
    "пришельцов"

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

    "Стрельба босса"

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

    "Спавн тарана"

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

    "Спавн стреляющих пришельцов"

    def spawn_soldier(self):
        gc = GameController
        if self.spawn_soldier_cooldown <= 0:
            player_x = self.player_to_track.pos[0]
            r = SoldierAlien(gc.aliens_bullets, gc.aliens, gc.all_sprites)
            r.set_pos(player_x, r.pos[1])
            self.spawn_soldier_cooldown = 240


"Спавн монет"


class Coin(Alien):
    def __init__(self, *groups):
        super().__init__(*groups, image_name='coin.png')
        self.speed = 3
        self.direction[1] = 1


"Класс, отвечающий за стрельбу каждого, смена вида стрелы"


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
            raise ValueError(f'Владелец должен относиться к классу Player или классу Alien или классу BossAlien')
        self.rect.centerx = x
        self.rect.bottom = y
        self.damage = damage
        self.speed = speed

    "Движение огня"

    def update(self):
        self.move(0, self.speed if self.target == Player else -self.speed)
        if self.rect.bottom <= 0 or self.rect.top >= GameSettings.screen_height or \
                self.rect.right <= 0 or self.rect.left >= GameSettings.screen_width:
            self.kill()


"Класс, отвечающий за движение игрока и его стрельбу"


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

    "Движение игрока"

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

    "Стрельба игрока, взависимости от типа коробля"

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


"Основная функция, которая отвечает за фоновую музыку, паузу, отрисовку разного рода информации"


def main():
    gc = GameController
    gs = GameSettings

    game_ui_sprites = pygame.sprite.Group()

    pygame.display.set_caption("Space War")
    clock = pygame.time.Clock()
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


"Запуск, подгрузка музыки"
if __name__ == '__main__':
    pygame.init()
    pygame.display.set_caption("Space War")

    SoundManager.load_sound('main_menu_theme', 'start.mp3')
    SoundManager.load_sound('start_game', 'start_engine.mp3')

    SoundManager.load_sound('alien_hit', 'strike.mp3')
    SoundManager.load_sound('background_music', 'fon_sound.mp3')
    SoundManager.load_sound('player_damage', 'damage.mp3')

    SoundManager.load_sound('game_over', 'game-over.mp3')

    input_nick()
    start_screen(889, 500)
