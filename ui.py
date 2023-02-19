import pygame

from typing import Tuple
from sprites import SWSprite


class Canvas(pygame.Surface):
    def __init__(self, surface: pygame.Surface, *elements):
        super().__init__(surface.get_size(), pygame.SRCALPHA)
        self.surface = surface
        self._elements = set(elements)

    @property
    def elements(self):
        return self._elements

    def copy(self):
        return Canvas(self.surface, self._elements)

    def add(self, *elements):
        self._elements |= set(elements)

    def remove(self, *elements):
        self._elements -= set(elements)

    def has(self, *elements) -> bool:
        return self._elements <= set(elements)

    def update(self, *args, **kwargs):
        for elem in self._elements:
            elem.update(*args, **kwargs)

    def draw(self):
        for elem in self._elements:
            elem.draw(self)
        self.surface.blit(self, (0, 0))

    def empty(self):
        self._elements = set()

"Класс, для добавления на картинку текст и использование её в роле кнопки"
class UIButton(SWSprite):
    def __init__(self, image: str | pygame.Surface, *groups,
                 text: str, font: pygame.font.Font, binding: callable,
                 color: Tuple[int, int, int] = (0, 0, 0),
                 antialias: bool = True):
        super().__init__(image, *groups)
        self.font = font
        self.text = text
        self.params = (antialias, color)
        self.binding = binding

    def is_clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1\
            and self.rect.collidepoint(*pygame.mouse.get_pos())

    def draw(self, surface):
        t = self.font.render(self.text, *self.params)
        width, height = self.size
        text_width, text_height = t.get_size()
        text_pos = (width - text_width) // 2, (height - text_height) // 2
        self.image.blit(t, text_pos)
        super().draw(surface)

    def update(self, *event):
        if event:
            event = event[0]
            if self.is_clicked(event):
                return self.binding()



"Класс, для обработки вводимого ника"
class TextInputBox(pygame.sprite.Sprite):
    def __init__(self, *groups, on_enter: callable):
        super().__init__(*groups)
        self.color = pygame.Color('white')
        self.pos = (50, 50)
        self.width = 550
        self.font = pygame.font.SysFont('SPACE MISSION', 100)
        self.cursor = False
        self.text = 'Введите ник...'
        self.on_enter = on_enter

    def draw(self, surface):
        if len(self.text) > 11:
            self.text = self.text[:11]
        text_surf = self.font.render(self.text, True, pygame.Color('DodgerBlue'))
        self.image = pygame.Surface((self.width + 10, text_surf.get_height() + 10))
        self.image.blit(text_surf, (10, 10))
        pygame.draw.rect(self.image, self.color, self.image.get_rect(), 3)
        self.rect = self.image.get_rect(topleft=self.pos)
        surface.blit(self.image, self.rect)

    def update(self, event):
        if not self.cursor and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.text = ""
            self.cursor = self.rect.collidepoint(event.pos)
        elif self.cursor and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.text and not self.text.isspace() and self.text != 'Введите ник...':
                    self.on_enter(self)
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode

