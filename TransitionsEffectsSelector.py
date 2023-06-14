import pygame

from Components import Button, get_hovered_color, Viewer
from Components import ScrollView
from Transitions import Transition

small_font = pygame.font.SysFont('arial', 15)

class TransitionsEffectsSelector:
    def __init__(self, win, pos, size):
        self.win = win
        self.pos = pos
        self.size = size

        self.is_transition_selected = True

        self.transition_btn = TransitionButton(self, self.win, self.pos, (100, 30))
        self.effect_btn = EffectButton(self, self.win, (self.pos[0]+self.transition_btn.size[0], self.pos[1]), self.transition_btn.size)

        self.transitions_selector = TransitionSelector(self, self.win, (self.pos[0], self.pos[1]+self.transition_btn.size[1]), (self.size[0], self.size[1]-self.transition_btn.size[1]))


    def frame(self, events, pos):
        self.transition_btn.frame(events, pos)
        self.effect_btn.frame(events, pos)

        if self.is_transition_selected:
            self.transitions_selector.frame(events, pos)



class TransitionButton(Button):
    BACKGROUND_COLOR = (18, 18, 18)

    def __init__(self, transitionsEffectsSelector, display, pos, size):
        super().__init__(display, pos, size, self.on_select)
        self.center = False

        self.transitionsEffectsSelector = transitionsEffectsSelector

        self.line_thickness = 2
        self.line_length = 20

    def on_select(self):
        self.transitionsEffectsSelector.is_transition_selected = True

    def blit(self):
        rect = pygame.Rect((self.pos[0], self.pos[1]), self.size)
        pygame.draw.rect(self.display, self.BACKGROUND_COLOR, rect, 0, 1)
        name = small_font.render("Transitions", True, (255, 255, 255))

        self.display.blit(name, (
            self.pos[0] + self.size[0]//2 - name.get_rect().width // 2,
            self.pos[1] + self.size[1]//2 - name.get_rect().height // 2))

        if self.transitionsEffectsSelector.is_transition_selected:
            pos = (self.pos[0]+self.size[0]//2, self.pos[1]+self.size[1]-self.line_thickness)
            pygame.draw.line(self.display, (255, 255, 255), (pos[0]-self.line_length, pos[1]), (pos[0]+self.line_length, pos[1]), width=self.line_thickness)

    def blit_hovered(self):
        rect = pygame.Rect((self.pos[0], self.pos[1]), self.size)
        pygame.draw.rect(self.display, get_hovered_color(self.BACKGROUND_COLOR, multiplier=1.5), rect, 0, 1)

        name = small_font.render("Transitions", True, (255, 255, 255))

        self.display.blit(name, (
            self.pos[0] + self.size[0] // 2 - name.get_rect().width // 2,
            self.pos[1] + self.size[1] // 2 - name.get_rect().height // 2))

        if self.transitionsEffectsSelector.is_transition_selected:
            pos = (self.pos[0]+self.size[0]//2, self.pos[1]+self.size[1]-self.line_thickness)
            pygame.draw.line(self.display, (255, 255, 255), (pos[0]-self.line_length, pos[1]), (pos[0]+self.line_length, pos[1]), width=self.line_thickness)

class EffectButton(Button):
    BACKGROUND_COLOR = (18, 18, 18)

    def __init__(self, transitionsEffectsSelector, display, pos, size):
        super().__init__(display, pos, size, self.on_select)
        self.center = False

        self.transitionsEffectsSelector = transitionsEffectsSelector

        self.line_thickness = 2
        self.line_length = 20

    def on_select(self):
        self.transitionsEffectsSelector.is_transition_selected = False

    def blit(self):
        rect = pygame.Rect((self.pos[0], self.pos[1]), self.size)
        pygame.draw.rect(self.display, self.BACKGROUND_COLOR, rect, 0, 1)
        name = small_font.render("Effects", True, (255, 255, 255))

        self.display.blit(name, (
            self.pos[0] + self.size[0]//2 - name.get_rect().width // 2,
            self.pos[1] + self.size[1]//2 - name.get_rect().height // 2))

        if not self.transitionsEffectsSelector.is_transition_selected:
            pos = (self.pos[0]+self.size[0]//2, self.pos[1]+self.size[1]-self.line_thickness)
            pygame.draw.line(self.display, (255, 255, 255), (pos[0]-self.line_length, pos[1]), (pos[0]+self.line_length, pos[1]), width=self.line_thickness)

    def blit_hovered(self):
        rect = pygame.Rect((self.pos[0], self.pos[1]), self.size)
        pygame.draw.rect(self.display, get_hovered_color(self.BACKGROUND_COLOR, multiplier=1.5), rect, 0, 1)

        name = small_font.render("Effects", True, (255, 255, 255))

        self.display.blit(name, (
            self.pos[0] + self.size[0] // 2 - name.get_rect().width // 2,
            self.pos[1] + self.size[1] // 2 - name.get_rect().height // 2))

        if not self.transitionsEffectsSelector.is_transition_selected:
            pos = (self.pos[0]+self.size[0]//2, self.pos[1]+self.size[1]-self.line_thickness)
            pygame.draw.line(self.display, (255, 255, 255), (pos[0]-self.line_length, pos[1]), (pos[0]+self.line_length, pos[1]), width=self.line_thickness)


class TransitionSelector:
    def __init__(self, transitionsEffectsSelector, win, pos, size):
        self.transitionsEffectsSelector = transitionsEffectsSelector

        self.win = win
        self.pos = pos
        self.size = size

        self.scroll_view = ScrollView(self.win, self.pos, self.size, on_selected=self.on_drag_start, on_drag=self.on_drag, on_drag_stop=self.on_drag_stop)

        self.transitions_viewer = []
        transitions = Transition.__subclasses__()
        for transition in transitions:
            viewer = TransitionViewer(self.transitionsEffectsSelector, self.scroll_view.display, size=(self.size[0], 30), pos=(0, 0),
                                          delta_pos=self.scroll_view.pos, transition=transition)
            self.transitions_viewer.append(viewer)

        self.scroll_view.set_items(self.transitions_viewer)

        self.current_selected_transition = None

    def frame(self, events, pos):
        self.scroll_view.frame(events, pos)

    def on_drag_start(self, transition_viewer):
        self.current_selected_transition = transition_viewer
        cursor = pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND)
        pygame.mouse.set_cursor(*cursor)

    def on_drag(self, transition_viewer):
        pass

    def on_drag_stop(self, transition_viewer):
        self.current_selected_transition = None
        cursor = pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW)
        pygame.mouse.set_cursor(*cursor)


class TransitionViewer(Viewer):
    def __init__(self, transitionsEffectsSelector, display, pos, delta_pos, size, transition):
        super().__init__(display, pos, delta_pos, size)

        self.transition = transition
        tr = transition(display, None, None)
        self.text = tr.name
        del tr

        self.transitionsEffectsSelector = transitionsEffectsSelector

    def on_delete(self):
        self.transitionsEffectsSelector.videoEditor.delete_transition(self.transition)
