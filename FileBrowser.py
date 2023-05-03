import math

import pygame
from Components import Button
from Components import get_hovered_color
from Timeline import CutTemplate

title_font = pygame.font.SysFont('arial', 25)
small_font = pygame.font.SysFont('arial', 15)


class FileBrowser:
    BACKGROUND_COLOR = (18, 18, 18)

    def __init__(self, display, pos, size, videoEditor):
        self.main_display = display

        self.display = pygame.Surface(size)

        self.pos = pos
        self.size = size

        self.videoEditor = videoEditor

        self.nb_per_column = 4
        self.delta = 8

        self.video_viewer_size = self.size[0] // self.nb_per_column - self.delta - self.delta // self.nb_per_column, \
                                 self.size[0] // self.nb_per_column - self.delta - self.delta // self.nb_per_column

        self.video_viewers = []

        self.y_delta = 0

        self.add_video_btn = AddVideoButton(self.videoEditor, self.display, (self.size[0]/2, self.size[1] - 50),
                                              (100, 40))
        self.add_video_btn.parent_pos = self.pos

        self._start_pos = None
        self._current_video_viewer = None

        self.update()

    def update(self):
        self.video_viewers = []
        self.video_viewers.append(VideoViewer(self.display, self.pos, self.pos, self.video_viewer_size, is_cut_template=True))
        for video in self.videoEditor.project_data.videos:
            self.video_viewers.append(
                VideoViewer(self.display, self.pos, self.pos, self.video_viewer_size, video))

    def frame(self, events, mouse_pos):
        self.display.fill(self.BACKGROUND_COLOR)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.is_hovered(mouse_pos):
                    if event.button == 4:
                        self.y_delta += 5
                        if self.y_delta > 0:
                            self.y_delta = 0
                    elif event.button == 5:
                        self.y_delta -= 5

                    elif event.button == 1:

                        for viewer in self.video_viewers:
                            if viewer.hovered:
                                self._start_pos = mouse_pos
                                self._current_video_viewer = viewer

            if event.type == pygame.MOUSEBUTTONUP:
                if self._current_video_viewer:
                    if self.videoEditor.timeline.is_hovered(mouse_pos):
                        if self._current_video_viewer.is_cut_template:
                            self.videoEditor.timeline.add_cut_template(0, self.videoEditor.project_data.length)
                        else:
                            t_object = self.videoEditor.timeline.get_video_at_position(self.videoEditor.timeline.x_to_frame(mouse_pos[0]))
                            if type(t_object) is CutTemplate:
                                self.videoEditor.show_video_cutter(self._current_video_viewer.video, t_object)
                            else:
                                self.videoEditor.timeline.add_video(self.videoEditor.timeline.get_ghost_object().start, self._current_video_viewer.video)

                    self.videoEditor.timeline.hide_ghost_object()

                self._start_pos = None
                self._current_video_viewer = None

        for i, video_viewer in enumerate(self.video_viewers):
            y = i // self.nb_per_column
            x = i - (y * self.nb_per_column)
            video_viewer.pos = (
                x * self.video_viewer_size[0] + self.delta * (x + 1),
                y * self.video_viewer_size[1] + self.delta * (y + 1) + self.y_delta)
            video_viewer.frame(events, mouse_pos)

        self.add_video_btn.frame(events, mouse_pos)

        self.main_display.blit(self.display, self.pos)

        if self._start_pos:  # on drag
            pos = (mouse_pos[0] - (self._start_pos[0] - self._current_video_viewer.pos[0]),
                   mouse_pos[1] - (self._start_pos[1] - self._current_video_viewer.pos[1]))

            if self.videoEditor.timeline.is_hovered(mouse_pos):
                if self._current_video_viewer.is_cut_template:
                    self.videoEditor.timeline.show_ghost_object(mouse_pos, self.videoEditor.project_data.length, (255, 255, 255))
                else:
                    self.videoEditor.timeline.show_ghost_object(mouse_pos, self._current_video_viewer.video.length,
                                                                (255, 255, 255),
                                                                fps=self._current_video_viewer.video.fps)
            else:
                self.videoEditor.timeline.hide_ghost_object()

            if self._current_video_viewer.is_cut_template:
                pygame.draw.rect(self.main_display, (255, 255, 255),pygame.Rect(pos, (self._current_video_viewer.size[0], int(1080 * (
                                                              self._current_video_viewer.size[0]) / 1920) * 1.3)))
            else:
                self.main_display.blit(pygame.transform.scale(self._current_video_viewer.video.mid_frame,
                                                          (self._current_video_viewer.size[0], int(1080 * (self._current_video_viewer.size[0]) / 1920)*1.3)), pos)


    def is_hovered(self, mouse_pos):
        if self.pos[0] <= mouse_pos[0] <= self.pos[0] + self.size[0] and self.pos[1] <= mouse_pos[1] <= self.pos[1] + \
                self.size[1]:
            return True
        return False


class VideoViewer:
    HOVERED_COLOR = (31, 31, 31)
    BACKGROUND_COLOR = (18, 18, 18)

    def __init__(self, display, pos, parent_pos, size, video=None, is_cut_template=False):
        self.display = display
        self.parent_pos = parent_pos
        self.pos = pos
        self.size = size

        self.video = video

        self.hovered = False

        self.is_cut_template = is_cut_template

    def frame(self, events, mouse_pos):
        self.hovered = self.is_hovered(mouse_pos)
        if self.hovered:
            rect = pygame.Rect(self.pos, self.size)
            pygame.draw.rect(self.display, get_hovered_color(self.BACKGROUND_COLOR), rect, 0, 10)
        rect = pygame.Rect(self.pos, self.size)
        pygame.draw.rect(self.display, self.BACKGROUND_COLOR, rect, 3, 10)

        title = self.video.title if not self.is_cut_template else "Cut Template"
        if len(title) > 14:
            title = title[:14] + "..."
        name = small_font.render(title, True, (255, 255, 255))

        self.display.blit(name, (
            self.pos[0] + self.size[0] / 2 - name.get_rect().width / 2,
            self.pos[1] + self.size[1] - name.get_rect().height))

        if self.is_cut_template:
            rect = pygame.Rect(self.pos,  (self.size[0], int(1080*(self.size[0])/1920)*1.3))
            pygame.draw.rect(self.display, (255, 255, 255), rect, 0, 10)
        else:
            self.display.blit(pygame.transform.scale(self.video.mid_frame, (self.size[0], int(1080*(self.size[0])/1920)*1.3)), self.pos)

        if self.hovered:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.on_click()

    def is_hovered(self, mouse_pos):
        pos = self.pos[0] + self.parent_pos[0], self.pos[1] + self.parent_pos[1]
        if pos[0] <= mouse_pos[0] <= pos[0] + self.size[0] and pos[1] <= mouse_pos[1] <= pos[1] + \
                self.size[1]:
            return True
        return False

    def on_click(self):
        pass



class AddVideoButton(Button):
    BACKGROUND_COLOR = (48, 48, 48)

    def __init__(self, videoEditor, display, pos, size):
        super().__init__(display, pos, size, self.add_video)
        self.center = True

        self.videoEditor = videoEditor

    def add_video(self):
        self.videoEditor.add_video()

    def blit(self):
        rect = pygame.Rect((self.pos[0] - self.size[0] / 2, self.pos[1] - self.size[1] / 2), self.size)
        pygame.draw.rect(self.display, self.BACKGROUND_COLOR, rect, 0, 1)
        pygame.draw.rect(self.display, (255, 255, 255), rect, 1, 1)

        name = small_font.render("Choose Media", True, (255, 255, 255))

        self.display.blit(name, (
            self.pos[0] - name.get_rect().width / 2,
            self.pos[1] - name.get_rect().height / 2))

    def blit_hovered(self):
        rect = pygame.Rect((self.pos[0] - self.size[0] / 2, self.pos[1] - self.size[1] / 2), self.size)
        pygame.draw.rect(self.display, get_hovered_color(self.BACKGROUND_COLOR), rect, 0, 1)
        pygame.draw.rect(self.display, (255, 255, 255), rect, 1, 1)

        name = small_font.render("Choose Media", True, (255, 255, 255))

        self.display.blit(name, (
            self.pos[0] - name.get_rect().width / 2,
            self.pos[1] - name.get_rect().height / 2))