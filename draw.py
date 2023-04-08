import pygame

from sprites import SWSprite

"Функция, для отрисовки текста и количество очков"


def draw_text(screen, string, size, pos):
    font = pygame.font.SysFont('SPACE MISSION', size)
    text = font.render(string, True, (0, 255, 0))
    screen.blit(text, pos)


"Функция, для отрисовки уровня здоровья"


def draw_health(screen, entity, x, y, width, height):
    heart = SWSprite('heart.png')
    heart.rect.center = x, y + height // 2

    h = max(0, entity.health) / type(entity).health
    health_size = h * width
    fill_line = pygame.Rect(x, y, health_size, height)
    fill_outline = pygame.Rect(x, y, width, height)
    if h > 0.5:
        pygame.draw.rect(screen, 'green', fill_line)
    elif h > 0.2:
        pygame.draw.rect(screen, 'dark orange', fill_line)
    else:
        pygame.draw.rect(screen, 'red', fill_line)
    pygame.draw.rect(screen, 'red', fill_outline, 2)
    heart.draw(screen)


"Функция, для отрисовки количества монет"


def draw_coin(screen, count):
    coin_draw = SWSprite('coin_draw.png')
    coin_draw.set_pos(580, 47)

    draw_text(screen, ': ', 45, (622, 50))
    draw_text(screen, str(count), 45, (650, 50))
    coin_draw.draw(screen)
