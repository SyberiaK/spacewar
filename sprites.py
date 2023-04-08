from pygame import Surface
from pygame.sprite import Sprite, Group

from managers import FileManager

"Класс, для отрисовки в игре спрайтов"


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


"Класс, для отрисовки в игре картинки GIF"


class AnimatedSprite(Sprite):
    def __init__(self, frames, *groups, frame_rate: int, update_rate: int):
        super().__init__(*groups)
        self.frames = frames
        self.frame_rate = frame_rate
        self.update_rate = update_rate
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect()

    def update(self):
        frame_step = self.update_rate // self.frame_rate
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
