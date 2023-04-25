import copy

import pygame


def get_hovered_color(color):
    n = 1.2
    return color[0] * n, color[1] * n, color[2] * n

class ScrollView:

    def __init__(self, display, pos, size):
        self.main_display = display
        self.display = pygame.Surface(size)

        self.pos = pos
        self.size = size

        self.items = []
        self.height = 0

        self.y_delta = 0

        self.background_color = (51, 51, 51)

    def frame(self, camera_delta, events, pos):
        rect = pygame.Rect(0, 0, self.size[0], self.size[1])
        pygame.draw.rect(self.display, self.background_color, rect, 0, 0)  # Background

        if self.is_hovered(pos):
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:
                        self.y_delta += 5
                        if self.y_delta > 0:
                            self.y_delta = 0
                    elif event.button == 5:
                        self.y_delta -= 5
        current_y_pos = 0
        for i, item in enumerate(self.items):
            item.parent_pos = self.pos
            item.pos = (0, current_y_pos + self.y_delta)
            item.delta_pos = self.pos
            if item.is_hovered(pos):
                item.hovered = True
            else:
                item.hovered = False
            current_y_pos += item.size[1]
            item.frame(camera_delta, events, pos)

        self.main_display.blit(pygame.transform.scale(self.display, self.size), self.pos)

        return True

    def is_hovered(self, mouse_pos):
        if self.pos[0] <= mouse_pos[0] <= self.pos[0] + self.size[0] and self.pos[1] <= mouse_pos[1] <= self.pos[1] + \
                self.size[1]:
            return True
        return False

    def calculate_height(self):
        height = 0
        for item in self.items:
            height += item.size[1]
        self.height = height

    def set_items(self, items):
        self.items = items
        self.calculate_height()

class Button:
    def __init__(self, display, pos, size, on_pressed):
        self.display = display
        self.pos = pos
        self.size = size

        self._on_pressed = on_pressed

        self.parent_pos = (0, 0)

        self.center = True  # is the given position is the center or the top left of the button

        self._is_hovered = False

        self.click_check = True

    def frame(self, events, pos):
        self._is_hovered = self.is_hovered(pos)
        if self.click_check:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self._is_hovered:
                            self._on_pressed()
                            return False

        if self._is_hovered:
            self.blit_hovered()
        else:
            self.blit()
        return True

    def blit(self):
        pass

    def blit_hovered(self):
        self.blit()

    def is_hovered(self, mouse_pos):
        if self.center:
            if self.pos[0] - self.size[0] / 2 <= mouse_pos[0] - self.parent_pos[0] <= self.pos[0] + self.size[0] / 2 and \
                    self.pos[1] - self.size[
                1] / 2 <= mouse_pos[1] - self.parent_pos[1] <= self.pos[1] + \
                    self.size[1] / 2:
                return True
        else:
            if self.pos[0] <= mouse_pos[0] - self.parent_pos[0] <= self.pos[0] + self.size[0] and self.pos[1] <= \
                    mouse_pos[1] - self.parent_pos[1] <= self.pos[1] + self.size[1]:
                return True
        return False

    def get_hovered_image(self, original):
        image = copy.copy(original)
        arr = pygame.surfarray.pixels3d(image)
        arr //= 2
        del arr
        return image


