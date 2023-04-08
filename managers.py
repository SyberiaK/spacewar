from pathlib import Path
from PIL import Image, ImageSequence
import pygame.image as pg_image
from pygame.mixer import Sound
import sqlite3

"Класс, отвечающий за обработку картинок, GIF картинок, баз данных и музыки"


class FileManager:
    DATA_PATH = Path.cwd() / 'data'

    SPRITES_PATH = DATA_PATH / 'sprites'

    SOUNDS_PATH = DATA_PATH / 'sounds'

    BASE_PATH = DATA_PATH / 'Result'

    @classmethod
    def load_image(cls, name, color_key=None):
        path = cls.SPRITES_PATH / name
        if not path.exists():
            raise FileNotFoundError(f"Файл с изображением '{name}' по пути '{path}' не найден")

        image = pg_image.load(path)
        if color_key is not None:
            image = image.convert()
            image.set_colorkey(image.get_at((0, 0)) if color_key == -1 else color_key)
        else:
            image = image.convert_alpha()
        return image

    @classmethod
    def load_gif_frames(cls, name: str, color_key=None):
        path = cls.SPRITES_PATH / name
        if not path.exists():
            raise FileNotFoundError(f"Файл с изображением '{name}' по пути '{path}' не найден")

        gif_image = Image.open(path)
        if gif_image.format != 'GIF' or not gif_image.is_animated:
            raise ValueError(f"Файл '{name}' по пути '{path}' не является анимированным изображением формата GIF")

        frames = []
        for frame in ImageSequence.Iterator(gif_image):
            frame = frame.convert('RGBA')
            pygame_frame = pg_image.fromstring(frame.tobytes(), frame.size, frame.mode)

            if color_key is not None:
                pygame_frame = pygame_frame.convert()
                pygame_frame.set_colorkey(pygame_frame.get_at((0, 0)) if color_key == -1 else color_key)
            else:
                pygame_frame = pygame_frame.convert_alpha()

            frames.append(pygame_frame)
        return frames

    @classmethod
    def load_sound(cls, name):
        path = cls.SOUNDS_PATH / name
        if not path.exists():
            raise FileNotFoundError(f"Файл со звуком '{name}' по пути '{path}' не найден")

        return Sound(path)

    @classmethod
    def load_base(cls, name):
        path = cls.BASE_PATH / name
        if not path.exists():
            raise FileNotFoundError(f"Файл с базой данных '{name}' по пути '{path}' не найден")

        return sqlite3.connect(path)


"Класс, отвечающий за работу с музыкой, для дальнейшего удобного использования"


class SoundManager:
    sounds: dict[str, Sound] = {}
    playing_loops: list[str] = []

    @classmethod
    def load_sound(cls, name: str, sound: str | Sound):
        if isinstance(sound, str):
            sound = FileManager.load_sound(sound)
        cls.sounds[name] = sound

    @classmethod
    def play_sound(cls, name, *, volume: float = 1, loop: bool = False):
        sound = cls.sounds[name]
        sound.set_volume(volume)
        if loop:
            cls.playing_loops.append(name)
        sound.play(-1 if loop else 0)

    @classmethod
    def stop_sound(cls, name):
        cls.sounds[name].stop()
        cls.playing_loops.remove(name)
