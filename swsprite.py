from pygame import Surface
from pygame.sprite import Sprite, Group

from managers import FileManager


class SWSprite(Sprite):
    def __init__(self, image: str | Surface, *groups: Group):
        super().__init__(*groups)
        if isinstance(image, Surface):
            self.image = image
        elif isinstance(image, str):
            self.image = FileManager.load_image(image)
        else:
            raise TypeError('Картинка может быть представлена только в виде строки пути или Surface')
        self.rect = self.image.get_rect()

    def change_image(self, image: str | Surface):
        if isinstance(image, Surface):
            self.image = image
        elif isinstance(image, str):
            self.image = FileManager.load_image(image)
        else:
            raise TypeError('Картинка может быть представлена только в виде строки пути или Surface')

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
