import random
from pathlib import Path

import pygame
import sys

FPS = 60
SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = 750, 1000
BLACK = pygame.Color('black')


def terminate():
    pygame.quit()
    sys.exit()


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


class SWSprite(pygame.sprite.Sprite):
    image_name = None

    def __init__(self, image_name: str | None, *groups: pygame.sprite.Group):
        if image_name is None:
            if self.image_name is None:
                raise TypeError(f"{type(self)}.__init__() missing 1 required positional argument: 'image_name'")
            image_name = self.image_name

        super().__init__(*groups)
        self.image = FileManager.load_image(image_name)
        self.rect = self.image.get_rect()

    def pos(self):
        return self.rect.topleft()

    def size(self):
        return self.rect.size

    def move(self, x, y):
        self.rect = self.rect.move(x, y)

    def set_pos(self, x, y):
        self.rect.topleft = x, y


class Alien(SWSprite):
    image_name = 'alien2.png'

    def __init__(self, *groups):
        super().__init__(None, *groups)
        self.speed = None
        self.to_start()

    def to_start(self):
        x = random.randrange(SCREEN_WIDTH - self.rect.width)
        y = random.randrange(-100, -30)
        self.set_pos(x, y)
        self.speed = random.randrange(1, 9)

    def update(self):
        self.move(0, self.speed)
        if self.rect.top >= SCREEN_HEIGHT or self.rect.right <= 0 or self.rect.left >= SCREEN_WIDTH:
            self.to_start()


class Player(SWSprite):
    image_name = "spaceX.png"

    def __init__(self, *groups):
        super().__init__(None, *groups)
        self.speed = 8
        self.rect.centerx = SCREEN_WIDTH / 2
        self.rect.bottom = SCREEN_HEIGHT - self.speed

    def update(self):
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
            if rect_check.left <= 0 or rect_check.bottom >= SCREEN_HEIGHT:
                direction[1] = 0

            self.move(*(d * speed for d in direction))


def main():
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("Space War")
    clock = pygame.time.Clock()
    all_sprites = pygame.sprite.Group()

    player = Player(all_sprites)
    for i in range(8):
        Alien(all_sprites)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN:
                player.update()
        screen.fill(BLACK)
        all_sprites.update()
        all_sprites.draw(screen)
        clock.tick(FPS)
        pygame.display.flip()


if __name__ == '__main__':
    main()
