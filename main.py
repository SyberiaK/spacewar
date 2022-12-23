import random

import pygame
import os
import sys


def load_image(name):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    return image


class Alien(pygame.sprite.Sprite):
    image_alien = load_image('alien2.png')

    def __init__(self):
        super().__init__(all_sprites)
        self.image = self.image_alien.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(1050 - self.rect.width)
        self.rect.y = random.randrange(-100, -30)
        self.speed = random.randrange(1, 9)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > 1010 or self.rect.left < -30 or self.rect.right > 750:
            self.rect.x = random.randrange(1050 - self.rect.width)
            self.rect.y = random.randrange(-100, -30)
            self.speed = random.randrange(1, 9)


class Player(pygame.sprite.Sprite):
    image_player = load_image("spaceX.png")

    def __init__(self):
        super().__init__(all_sprites)
        self.image = self.image_player.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.centerx = 750 / 2
        self.rect.bottom = 1015
        self.speed = 0

    def update(self):
        self.speed = 0
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_a]:
            self.speed = -8
        if keystate[pygame.K_d]:
            self.speed = 8
        self.rect.x += self.speed
        if self.rect.right > 780:
            self.rect.right = 780
        if self.rect.left < -30:
            self.rect.left = -30


if __name__ == '__main__':
    pygame.init()
    FPS = 60
    size = width, height = 750, 1000
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("Space War")
    clock = pygame.time.Clock()
    all_sprites = pygame.sprite.Group()
    player = Player()
    for i in range(8):
        alien = Alien()
    running = True
    while running:
        screen.fill((0, 0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        all_sprites.update()
        all_sprites.draw(screen)
        clock.tick(FPS)
        pygame.display.flip()
    pygame.quit()