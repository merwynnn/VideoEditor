import copy

import pygame

small_font = pygame.font.SysFont('arial', 15)


def get_hovered_color(color, multiplier=1):
    n = 1.2 * multiplier
    return color[0] * n, color[1] * n, color[2] * n

class ScrollView:

    def __init__(self, display, pos, size, on_selected=None, on_drag=None, on_drag_stop=None):
        self.main_display = display
        self.display = pygame.Surface(size)

        self.pos = pos
        self.size = size

        self.items = []
        self.height = 0

        self.y_delta = 0

        self.background_color = (18, 18, 18)

        self._current_selected_viewer = None

        self.on_selected = on_selected
        self.on_drag = on_drag
        self.on_drag_stop = on_drag_stop

    def frame(self, events, pos):
        rect = pygame.Rect(0, 0, self.size[0], self.size[1])
        pygame.draw.rect(self.display, self.background_color, rect, 0, 0)  # Background

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.is_hovered(pos):
                    if event.button == 4:
                        self.y_delta += 5
                        if self.y_delta > 0:
                            self.y_delta = 0
                    elif event.button == 5:
                        self.y_delta -= 5

                if event.button == 1:
                    for viewer in self.items:
                        if viewer.hovered:
                            self._current_selected_viewer = viewer
                            if self.on_selected:
                                self.on_selected(self._current_selected_viewer)
                            break

            if event.type == pygame.MOUSEBUTTONUP:
                if self._current_selected_viewer:
                    if self.on_drag_stop:
                        self.on_drag_stop(self._current_selected_viewer)
                    self._current_selected_viewer = None

        if self._current_selected_viewer:
            if self.on_drag:
                self.on_drag(self._current_selected_viewer)

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
            item.frame(events, pos)

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


class Viewer:
    FOCUSED_COLOR = (64, 63, 63)

    def __init__(self, display, pos, delta_pos, size):

        self.display = display
        self.pos = pos
        self.delta_pos = delta_pos
        self.size = size

        self.hovered = False

        self.text = "Empty Viewer"

        self.parent_pos = (0, 0)

        self.show_delete_btn = True
        self.delete_button = DeleteButton(self.display, self.pos, (15, 15), self.on_delete)

    def frame(self, events, pos):
        if self.hovered:
            rect = pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
            pygame.draw.rect(self.display, self.FOCUSED_COLOR, rect, 0, 1)  # Background

        rect = pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
        pygame.draw.rect(self.display, (0, 0, 0), rect, 1, 1)

        text = small_font.render(self.text, True, (255, 255, 255))
        self.display.blit(text, (self.pos[0] + 10, self.pos[1] + self.size[1] / 2 - text.get_rect().height / 2))

        if self.show_delete_btn:
            if self.delete_button:
                self.delete_button.pos = (self.pos[0] + self.size[0] - 30, self.pos[1] + self.size[1] / 2)
                self.delete_button.parent_pos = self.parent_pos
                self.delete_button.frame(events, pos)

    def is_hovered(self, mouse_pos):
        if self.pos[0] + self.delta_pos[0] <= mouse_pos[0] <= self.pos[0] + self.delta_pos[0] + self.size[0] and \
                self.pos[1] + self.delta_pos[1] <= mouse_pos[1] <= self.pos[1] + self.delta_pos[1] + \
                self.size[1]:
            return True
        return False

    def on_delete(self):
        pass

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

class DeleteButton(Button):
    def __init__(self, display, pos, size, on_pressed):
        super().__init__(display, pos, size, on_pressed)
        self.color = (99, 99, 99)
        self.cross = pygame.image.load("Assets/cross.png").convert_alpha()
        self.cross = pygame.transform.scale(self.cross, self.size)

        self.cross_hovered = self.get_hovered_image(self.cross)

    def blit(self):
        self.display.blit(self.cross, (self.pos[0] - self.size[0] / 2, self.pos[1] - self.size[1] / 2))

    def blit_hovered(self):
        self.display.blit(self.cross_hovered, (self.pos[0] - self.size[0] / 2, self.pos[1] - self.size[1] / 2))
