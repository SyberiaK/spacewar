import pygame

from typing import Tuple
from sprites import SWSprite

"Класс, для добавления на картинку текст и использование её в роле кнопки"


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
        self.render_text()

    def render_text(self):
        if len(self.text) > 11:
            self.text = self.text[:11]
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
                        if self.text and self.text != 'Введите ник...':
                            self.on_enter(self)
                    elif event.key == pygame.K_BACKSPACE:
                        self.text = self.text[:-1]
                    else:
                        self.text += event.unicode
                    self.render_text()
