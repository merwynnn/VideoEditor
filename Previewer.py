import pygame


class Previewer:
    def __init__(self, win, pos, size):
        self.win = win
        self.pos = pos
        self.size = size

    def frame(self, events, mouse_pos):
        pygame.draw.rect(self.win, (0, 0, 0), pygame.Rect(self.pos, self.size))