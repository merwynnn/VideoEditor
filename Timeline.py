import random
import sys
import time
from itertools import chain

import pygame
from Components import get_hovered_color
import soundfile as sf
import numpy as np
import threading

title_font = pygame.font.SysFont('arial', 25)
small_font = pygame.font.SysFont('arial', 15)
v_small_font = pygame.font.SysFont('arial', 10)


class Timeline:
    BACKGROUND_COLOR = (18, 18, 18)

    def __init__(self, win, pos, size, videoEditor, preview=True):
        self.win = win
        self.pos = pos
        self.size = size

        self.videoEditor = videoEditor

        self.preview = preview

        self.timeline_objects = []

        self.zoom = 1
        self.zoom_factor = self.videoEditor.project_data.fps * 30  # nb of frames displayed on the timeline when zoom=1

        self.top_bar_height = 30

        handle_height = 6
        offset = (10, 25)
        self.handle = Handle(self.win,
                             pos=(self.pos[0] + offset[0], self.pos[1] + self.size[1] - handle_height - offset[1]),
                             size=(self.size[0] - offset[0] * 2, handle_height), view_limits=(0, self.zoom_factor),
                             length=self.videoEditor.project_data.length, zoom=self.zoom, zoom_factor=self.zoom_factor)

        self.cursor_pos = 0
        self.cursor = Cursor(self.win, pos=(self.pos[0], self.pos[1] + 9),
                             size=(15, self.size[1] - self.handle.size[1] - 9 - 40))

        self.main_audio = Audio(self, self.videoEditor.project_data.main_song, 1, 0,
                                self.videoEditor.project_data.length)
        self.timeline_objects.append(self.main_audio)

        for t_object in list(chain.from_iterable(self.videoEditor.project_data.rows)):
            t_object.timeline = self
            self.timeline_objects.append(t_object)

        self.selected_timeline_objects = []

        self.video_object_at_cursor = None

        self.hovered_cut_right = None
        self.hovered_cut_left = None

        self._is_cursor_moving = False
        self._is_moving_objects = False
        self._is_moving_cuts = False
        self._start_frame = None

        self._current_ghost_object = None

        self._start_play_frame = 0

    def frame(self, events, mouse_pos):
        pygame.draw.rect(self.win, self.BACKGROUND_COLOR,
                         pygame.Rect((self.pos[0] - 5, self.pos[1]), (self.size[0] + 10, self.size[1])))

        self.handle.hovered = self.handle.is_hovered(mouse_pos)
        hovered = self.is_hovered(mouse_pos)

        if self.videoEditor.is_playing:
            self.cursor_pos = (
                                      pygame.mixer.music.get_pos() / 1000) * self.videoEditor.project_data.fps + self._start_play_frame
            self.load_at_cursor_position()

        hovered_timeline_object = self.get_hovered_timeline_object(mouse_pos)
        is_top_hovered = self.is_top_hovered(mouse_pos)

        if not self._is_moving_cuts:
            cut_hovered_delta = 1
            self.hovered_cut_right, self.hovered_cut_left = None, None
            if not is_top_hovered:
                if not self.handle.hovered:
                    if hovered_timeline_object:
                        mouse_frame = self.x_to_frame(mouse_pos[0])
                        if hovered_timeline_object.start - cut_hovered_delta <= mouse_frame <= hovered_timeline_object.start + cut_hovered_delta:
                            self.hovered_cut_right = hovered_timeline_object
                            # Get timeline object next to it
                            if hovered_timeline_object in self.videoEditor.project_data.rows[
                                hovered_timeline_object.row]:
                                timeline_object_index = self.videoEditor.project_data.rows[
                                    hovered_timeline_object.row].index(hovered_timeline_object)
                                if timeline_object_index != 0:
                                    left_timeline_object = \
                                    self.videoEditor.project_data.rows[hovered_timeline_object.row][
                                        timeline_object_index - 1]
                                    if self.hovered_cut_right.start - 1 <= left_timeline_object.end <= self.hovered_cut_right.start:
                                        self.hovered_cut_left = left_timeline_object

                        elif hovered_timeline_object.end - cut_hovered_delta <= mouse_frame <= hovered_timeline_object.end + cut_hovered_delta:
                            self.hovered_cut_left = hovered_timeline_object
                            # Get timeline object next to it
                            if hovered_timeline_object in self.videoEditor.project_data.rows[
                                hovered_timeline_object.row]:
                                timeline_object_index = self.videoEditor.project_data.rows[
                                    hovered_timeline_object.row].index(hovered_timeline_object)
                                if timeline_object_index != len(
                                        self.videoEditor.project_data.rows[hovered_timeline_object.row]) - 1:
                                    right_timeline_object = \
                                    self.videoEditor.project_data.rows[hovered_timeline_object.row][
                                        timeline_object_index + 1]
                                    if self.hovered_cut_left.end <= right_timeline_object.start <= self.hovered_cut_left.end + 1:
                                        self.hovered_cut_right = right_timeline_object

            if self.hovered_cut_right or self.hovered_cut_left:
                cursor = pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND)
                pygame.mouse.set_cursor(*cursor)
            else:
                cursor = pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW)
                pygame.mouse.set_cursor(*cursor)

        keys = pygame.key.get_pressed()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_x:
                    # Cut
                    timeline_object = self.get_video_at_position(self.cursor_pos)
                    if timeline_object in self.selected_timeline_objects:
                        self.remove_object_from_timeline(timeline_object)
                        t1, t2 = timeline_object.cut(self.cursor_pos)
                        self.add_object_to_timeline(t1)
                        self.add_object_to_timeline(t2)
                        self.selected_timeline_objects.remove(timeline_object)
                        self.selected_timeline_objects.append(t2)
                if event.key == pygame.K_DELETE:
                    for selected_obj in self.selected_timeline_objects:
                        self.remove_object_from_timeline(selected_obj)
                    self.selected_timeline_objects = []
            if event.type == pygame.MOUSEBUTTONDOWN:
                if hovered:
                    if event.button == 4:
                        if self.zoom * 0.9 > 0.01:
                            self.zoom *= 0.9
                    elif event.button == 5:
                        if self.zoom * 1.1 < 3:
                            self.zoom *= 1.1
                    if event.button == 1:
                        if is_top_hovered:
                            if self.cursor.is_hovered(mouse_pos):
                                self._is_cursor_moving = True
                            else:
                                self.cursor_pos = self.x_to_frame(mouse_pos[0])
                                self.videoEditor.previewer.has_cursor_moved = True
                                self._start_play_frame = self.cursor_pos
                                self.load_at_cursor_position()
                        elif not self.handle.hovered:
                            obj = hovered_timeline_object
                            if obj:
                                if self.hovered_cut_right or self.hovered_cut_left:
                                    self._is_moving_cuts = True
                                else:
                                    if not keys[pygame.K_LCTRL]:
                                        self.selected_timeline_objects = []
                                    self.selected_timeline_objects.append(obj)
                                    self.timeline_objects.remove(obj)
                                    self.timeline_objects.append(obj)

                                    self._is_moving_objects = True
                                    self._start_frame = self.x_to_frame(mouse_pos[0])
                                    for t_object in self.selected_timeline_objects:
                                        t_object.stored_start = t_object.start

                            else:
                                self.selected_timeline_objects = []

            if event.type == pygame.MOUSEBUTTONUP:
                self._is_moving_cuts = False
                self._is_cursor_moving = False
                if self._is_moving_objects:
                    self._is_moving_objects = False
                    for t_object in self.selected_timeline_objects:
                        if type(t_object) != Audio:
                            self.remove_object_from_timeline(t_object)
                            self.add_object_to_timeline(t_object)

        if self._is_cursor_moving:
            self.cursor_pos = self.x_to_frame(mouse_pos[0])
            self.videoEditor.previewer.has_cursor_moved = True
            self._start_play_frame = self.cursor_pos
            self.load_at_cursor_position()

        if self._is_moving_objects:
            for t_object in self.selected_timeline_objects:
                mouse_pos_frame = self.x_to_frame(mouse_pos[0])
                new_start = t_object.stored_start + (mouse_pos_frame - self._start_frame)
                t_object.end = new_start + (t_object.end - t_object.start)
                t_object.start = new_start

        if self._is_moving_cuts:
            mouse_frame = self.x_to_frame(mouse_pos[0])
            if self.hovered_cut_right:
                if isinstance(self.hovered_cut_right, Video):
                    self.hovered_cut_right.video_start = self.hovered_cut_right.get_relative_frame_index(mouse_frame)
                self.hovered_cut_right.start = mouse_frame
            if self.hovered_cut_left:
                if isinstance(self.hovered_cut_left, Video):
                    self.hovered_cut_left.video_end = self.hovered_cut_left.get_relative_frame_index(mouse_frame)
                self.hovered_cut_left.end = mouse_frame

        self.handle.zoom = self.zoom
        self.handle.frame(events, mouse_pos)

        # Drawing background Lines
        time_color = (71, 71, 71)
        if self.zoom < 0.1:
            start = int(self.handle.view_limits[0]) - 1
            end = int(self.handle.view_limits[1]) + 1
            for i in range(start, end):
                t = small_font.render(str(i), True, time_color)
                pos = (self.frame_to_pos(i), self.pos[1] + 5)
                self.win.blit(t, (pos[0] - t.get_rect().width / 2, pos[1]))
                pygame.draw.line(self.win, time_color, (pos[0], pos[1] + t.get_rect().height + 5),
                                 (self.frame_to_pos(i), self.pos[1] + self.size[1] - 15), 2)
        else:
            fps = self.videoEditor.project_data.fps
            start = int(self.handle.view_limits[0] / fps) - 1
            end = int(self.handle.view_limits[1] / fps) + 1
            for i in range(start, end):
                t = small_font.render(str(i), True, time_color)
                pos = (self.time_to_pos(i), self.pos[1] + 5)
                self.win.blit(t, (pos[0] - t.get_rect().width / 2, pos[1]))
                pygame.draw.line(self.win, time_color, (pos[0], pos[1] + t.get_rect().height + 5),
                                 (self.time_to_pos(i), self.pos[1] + self.size[1] - 15), 2)

        i = 0
        for timeline_object in self.timeline_objects:
            if self.handle.view_limits[0] <= timeline_object.start <= self.handle.view_limits[1] or \
                    self.handle.view_limits[0] <= timeline_object.end <= self.handle.view_limits[1] or (
                    timeline_object.start <= self.handle.view_limits[0] and timeline_object.end >=
                    self.handle.view_limits[1]):
                i += 1
                timeline_object.frame(events, mouse_pos,
                                      selected=True if timeline_object in self.selected_timeline_objects else False)

        if self.cursor_pos < 0:
            self.cursor_pos = 0
        if self.cursor_pos > self.videoEditor.project_data.length:
            self.cursor_pos = self.videoEditor.project_data.length
        self.cursor.set_pos_x(self.frame_to_pos(self.cursor_pos))
        self.cursor.frame(events, mouse_pos)

    def is_hovered(self, mouse_pos):
        if self.pos[0] <= mouse_pos[0] <= self.pos[0] + self.size[0] and self.pos[1] <= mouse_pos[1] <= self.pos[1] + \
                self.size[1]:
            return True
        return False

    def is_top_hovered(self, mouse_pos):  # is hovered for the top of the timeline (cursor)
        if self.pos[0] <= mouse_pos[0] <= self.pos[0] + self.size[0] and self.pos[1] <= mouse_pos[1] <= self.pos[
            1] + self.top_bar_height:
            return True
        return False

    def time_to_pos(self, time):
        e = (self.handle.view_limits[1] - self.handle.view_limits[0]) / self.videoEditor.project_data.fps
        t = time - (self.handle.view_limits[0] / self.videoEditor.project_data.fps)

        return (self.size[0] * t) / e + self.pos[0]

    def frame_to_pos(self, frame):
        s = int(self.handle.view_limits[0])
        e = int(self.handle.view_limits[1]) - s
        t = frame - s

        return (self.size[0] * t) / e + self.pos[0]

    def x_to_frame(self, x):
        e = self.handle.view_limits[1] - self.handle.view_limits[0]
        return int(((x - self.pos[0]) * e / self.size[0]) + self.handle.view_limits[0])

    def get_row_pos_size(self, row):
        y = 0
        for e in self.videoEditor.project_data.rows_size[:row]:
            y += e * self.videoEditor.project_data.row_factor
        return self.pos[1] + self.top_bar_height + y, self.videoEditor.project_data.rows_size[
            row] * self.videoEditor.project_data.row_factor

    def add_cut_template(self, f_start, f_end):
        t = CutTemplate(self, 0, f_start, f_end)
        self.add_object_to_timeline(t)

    def add_video(self, f_start, video_file, row=0):
        v = Video(self, video_file, row, start=f_start)
        self.add_object_to_timeline(v)
        self.load_at_cursor_position()

    def add_object_to_timeline(self, t_object):
        self.timeline_objects.append(t_object)
        l = len(self.videoEditor.project_data.rows[t_object.row])
        if l > 0:
            i = 0
            while t_object.start > self.videoEditor.project_data.rows[t_object.row][i].end:
                i += 1
                if l - 1 < i:
                    break
            self.videoEditor.project_data.rows[t_object.row].insert(i, t_object)
        else:
            self.videoEditor.project_data.rows[t_object.row].append(t_object)

    def remove_object_from_timeline(self, t_object):
        self.videoEditor.project_data.rows[t_object.row].remove(t_object)
        self.timeline_objects.remove(t_object)

    def get_video_at_position(self, frame):
        videos = self.videoEditor.project_data.rows[0]
        for video in videos:
            if video.start <= frame <= video.end:
                return video
        """
        while len(videos) > 1:
            i = len(videos) // 2
            if frame < videos[i].start:
                videos = videos[:i]
            elif videos[i].end < frame:
                videos = videos[i + 1:]
            else:
                return videos[i]
        if len(videos) > 0:
            if videos[0].start <= frame <= videos[0].end:
                return videos[0]
        """
        return None

    def show_ghost_object(self, mouse_pos, length, color, fps=None):
        start = self.x_to_frame(mouse_pos[0])
        end = start + length
        if not self._current_ghost_object:
            self._current_ghost_object = GhostObject(self, 0, start, end, color, fps)
            self.timeline_objects.append(self._current_ghost_object)
        self._current_ghost_object.start = start
        self._current_ghost_object.end = end

    def hide_ghost_object(self):
        if self._current_ghost_object:
            self.timeline_objects.remove(self._current_ghost_object)
            self._current_ghost_object = None

    def get_ghost_object(self):
        return self._current_ghost_object

    def load_at_cursor_position(self):
        if self.videoEditor.pre_load:
            self.video_object_at_cursor = self.get_video_at_position(self.cursor_pos)
            if self.video_object_at_cursor:
                t = threading.Thread(target=self.load_threaded)
                t.start()

    def load_threaded(self):
        self.video_object_at_cursor.video_file.load_at_frame(
            self.video_object_at_cursor.get_relative_frame_index(self.cursor_pos))

    def get_hovered_timeline_object(self, mouse_pos):
        for obj in self.timeline_objects:
            if obj.hovered:
                return obj
        return None


class TimelineObject:
    def __init__(self, timeline, row, start, end, color):
        self.timeline = timeline
        self.row = row
        self.start = start
        self.end = end
        self.color = color
        self.selected_color = (245, 217, 37)
        self.hovered = False

        self.stored_start = None  # used when moving object

    def frame(self, events, mouse_pos, selected=False):
        s = self.timeline.frame_to_pos(self.start)
        e = self.timeline.frame_to_pos(self.end)
        row_y, row_height = self.timeline.get_row_pos_size(self.row)
        pos = (s, row_y)
        size = (e - s, row_height)
        rect = pygame.Rect(pos, size)
        pygame.draw.rect(self.timeline.win, self.color, rect)

        offset = 2
        if selected:
            # On select
            rect = pygame.Rect((pos[0] - offset, pos[1] - offset), (size[0] + offset * 2, size[1] + offset * 2))
            pygame.draw.rect(self.timeline.win, self.selected_color, rect, width=2)

        self.hovered = True if pos[0] <= mouse_pos[0] <= pos[0] + size[0] and pos[1] <= mouse_pos[1] <= pos[1] + size[
            1] else False

        if self.timeline.hovered_cut_right is self:
            pygame.draw.line(self.timeline.win, (255, 0, 0), (pos[0] - offset, pos[1] - offset),
                             (pos[0] - offset, pos[1] + size[1] + offset), width=2)
        elif self.timeline.hovered_cut_left is self:
            pygame.draw.line(self.timeline.win, (255, 0, 0), (pos[0] + size[0], pos[1] - offset),
                             (pos[0] + size[0], pos[1] + size[1] + offset), width=2)
        self.top_frame(events, mouse_pos, pos, size)

    def top_frame(self, events, mouse_pos, row_pos, row_size):
        pass

    def get_length_with_fps(self, original_length, original_fps, targeted_fps):
        return (targeted_fps * original_length) // original_fps

    def __getstate__(self):
        state = self.__dict__.copy()
        # Don't pickle display
        try:
            del state["timeline"]

            state = self.get_state(state)
        except KeyError:
            pass

        return state

    def __setstate__(self, state):
        """ Called on load data from file (unpickle) """
        self.__dict__.update(state)
        self.set_state(state)

    def get_state(self, state):
        return state

    def set_state(self, state):
        pass



class Audio(TimelineObject):
    def __init__(self, timeline, audio_file, row, start, end):
        super().__init__(timeline, row, start, end, (41, 171, 56))
        self.audio_file = sf.SoundFile(audio_file)
        self.samples = self.audio_file.read()
        if len(self.samples.shape) > 1:
            # Average the two channels to get a mono signal
            self.samples = np.mean(self.samples, axis=1)
        self.samples = np.abs(self.samples)
        self.max = self.samples.max()

        self.audio_file.close()

    def top_frame(self, events, mouse_pos, row_pos, row_size):
        # optimization
        l = len(self.samples)
        d = int(l / row_size[0]) * 3
        for i in range(0, l, d):
            x = i * row_size[0] // l
            if row_pos[0] + x >= 0:
                y = self.samples[i] * row_size[1] // 2 * (1 / self.max) * 2
                start_pos = (row_pos[0] + x, row_pos[1] + row_size[1] // 2 - y // 2)
                end_pos = (row_pos[0] + x, row_pos[1] + row_size[1] // 2 + y // 2)
                pygame.draw.line(self.timeline.win, (255, 255, 255), start_pos, end_pos)
            if row_pos[0] + x > self.timeline.size[0] + self.timeline.pos[0]:
                break


class Video(TimelineObject):
    def __init__(self, timeline, video_file, row, start, end=None, video_start=0, video_end=None):
        # Scales the video length to be the right one even if the fps of the video is not the same as the project's fps
        if end is None:
            end = start + self.get_length_with_fps(video_file.length - video_start, video_file.fps,
                                                   timeline.videoEditor.project_data.fps)

        super().__init__(timeline, row, start, end,
                         (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

        self.video_file = video_file
        self.video_path = self.video_file.path

        self.video_start = None
        self.video_end = None
        self.calculate_video_start_end(video_start, video_end)

    def top_frame(self, events, mouse_pos, row_pos, row_size):
        if self.video_file and self.timeline.preview:
            video_size = self.video_file.mid_frame.get_size()
            w = (video_size[0] * row_size[1]) // video_size[1]
            nb = int(row_size[0] // w)
            if nb > 0:
                for i in range(nb):
                    self.timeline.win.blit(pygame.transform.scale(self.video_file.mid_frame, (w, row_size[1])),
                                           (row_pos[0] + i * w, row_pos[1]))
                if row_size[0] % w - row_size[0] != 0:
                    self.timeline.win.blit(
                        pygame.transform.scale(self.video_file.mid_frame, (row_size[0] % w, row_size[1])),
                        (row_pos[0] + nb * w, row_pos[1]))
            else:
                self.timeline.win.blit(
                    pygame.transform.scale(self.video_file.mid_frame, (row_size[0], row_size[1])),
                    (row_pos[0], row_pos[1]))

            for frame_index in self.video_file.video.keys():
                n = len(self.video_file.video[frame_index])
                f1 = self.get_absolute_frame_index(frame_index)
                f2 = self.get_absolute_frame_index(frame_index + n)
                pos1 = (self.timeline.frame_to_pos(f1), row_pos[1])
                pos2 = (self.timeline.frame_to_pos(f2), row_pos[1])
                pygame.draw.line(self.timeline.win, (255, 0, 0), pos1, pos2)

    def get_relative_frame_index(self, abs_frame):
        relative_pos = abs_frame - self.start
        return self.video_start + int((relative_pos * (self.video_end - self.video_start)) // (self.end - self.start))

    def get_absolute_frame_index(self, rel_frame):
        absolute_pos = int(
            ((rel_frame - self.video_start) * (self.end - self.start)) / (self.video_end - self.video_start))
        return absolute_pos + self.start

    def get_frame_at_pos(self, pos):
        frame_with_fps = self.get_relative_frame_index(pos)

        frame = self.video_file.get_frame(frame_with_fps)

        return frame

    def get_high_res_frame_at_pos(self, pos):
        frame_with_fps = self.get_relative_frame_index(pos)

        frame = self.video_file.get_high_res_frame(frame_with_fps)

        return frame

    def calculate_video_start_end(self, video_start=None, video_end=None):
        if video_start is not None:
            self.video_start = video_start
            self.video_end = self.video_start + self.get_length_with_fps(self.end - self.start,
                                                                         self.timeline.videoEditor.project_data.fps,
                                                                         self.video_file.fps)
        elif video_end is not None:
            self.video_start = video_end - self.get_length_with_fps(self.end - self.start,
                                                                    self.timeline.videoEditor.project_data.fps,
                                                                    self.video_file.fps)
            self.video_end = video_end

    def cut(self, pos):
        rel_pos = self.get_relative_frame_index(pos)
        t1 = Video(self.timeline, self.video_file, self.row, start=self.start, end=pos, video_start=self.video_start)
        # t1.video_end = rel_pos

        t2 = Video(self.timeline, self.video_file, self.row, start=pos, end=self.end)
        t2.video_start = rel_pos
        t2.video_end = self.video_end

        return t1, t2

    def get_state(self, state):
        del state["video_file"]
        return state

    def set_state(self, state):
        self.video_file = None

class CutTemplate(TimelineObject):
    def __init__(self, timeline, row, start, end):
        super().__init__(timeline, row, start, end,
                         (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

    def cut(self, pos):
        t1 = CutTemplate(self.timeline, self.row, start=self.start, end=pos)
        t1.color = self.color
        t2 = CutTemplate(self.timeline, self.row, start=pos, end=self.end)

        return t1, t2


class GhostObject(TimelineObject):
    def __init__(self, timeline, row, start, end, color, fps=None):
        background_color = timeline.BACKGROUND_COLOR
        if fps:
            end = start + self.get_length_with_fps((end - start), fps, timeline.videoEditor.project_data.fps)
        super().__init__(timeline, row, start, end, (
            (color[0] + background_color[0]) // 2, (color[1] + background_color[1]) // 2,
            (color[2] + background_color[2]) // 2))


class Handle:
    def __init__(self, win, pos, size, view_limits, length, zoom, zoom_factor):
        self.win = win
        self.pos = pos
        self.size = size
        self._default_size = size
        self.view_limits = view_limits  # X position (in seconds) of the start and end of what the user can see on the timeline
        self.length = length
        self.zoom = zoom
        self.zoom_factor = zoom_factor

        self.handle_start_end = (0, 0)

        self.hovered = False

        self._start_mouse_pos = None
        self._start_handle_pos = None
        self._start_view_limits = None

    def frame(self, events, pos):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.hovered:
                        self._start_mouse_pos = pos
                        self._start_handle_pos = self.handle_start_end
                        self._start_view_limits = self.view_limits
            if event.type == pygame.MOUSEBUTTONUP:
                self._start_mouse_pos = None
                self._start_handle_pos = None
                self._start_view_limits = None

        l = self.zoom_factor * self.zoom
        mid = (self.view_limits[1] + self.view_limits[0]) / 2
        self.view_limits = (mid - (l / 2), mid + (l / 2))

        if self._start_mouse_pos:  # on drag
            p1 = ((pos[0] - self.pos[0]) * self.win.get_width() / self.size[0])
            p2 = ((self._start_mouse_pos[0] - self.pos[0]) * self.win.get_width() / self.size[0])
            delta = p1 - p2
            delta = (delta * self.length / self.win.get_width())
            # delta = self.x_to_frame(pos[0]) - self.x_to_frame(self._start_mouse_pos[0])
            self.view_limits = (self._start_view_limits[0] + delta, self._start_view_limits[1] + delta)

        if self.view_limits[0] < 0:
            self.view_limits = (0, self.zoom * self.zoom_factor)
        if self.view_limits[1] > self.length:
            self.view_limits = (self.length - self.zoom * self.zoom_factor, self.length)
            if self.view_limits[0] < 0:
                self.view_limits = (0, self.view_limits[1])

        self.handle_start_end = (
            (self.view_limits[0] * self.size[0]) / self.length, (self.view_limits[1] * self.size[0]) / self.length)

        rect = pygame.Rect(
            (self.pos[0] + self.handle_start_end[0], self.pos[1]), (
                self.handle_start_end[1] - self.handle_start_end[0], self.size[1]))
        pygame.draw.rect(self.win, get_hovered_color((61, 61, 61)) if self.hovered else (61, 61, 61), rect, width=0,
                         border_radius=4)

    def is_hovered(self, mouse_pos):
        if self.pos[0] + self.handle_start_end[0] <= mouse_pos[0] <= self.pos[0] + self.handle_start_end[0] + \
                self.handle_start_end[1] - self.handle_start_end[0] and self.pos[1] <= mouse_pos[1] <= self.pos[1] + \
                self.size[1]:
            return True
        return False

    def x_to_frame(self, x):
        e = self.view_limits[1] - self.view_limits[0]
        return int(((x - self.pos[0]) * e / self.size[0]) + self.view_limits[0])


class Cursor:
    def __init__(self, win, pos, size):
        self.win = win
        self.pos = pos
        self.size = size

        self.color = (73, 88, 252)

    def frame(self, events, pos):
        main_point = (self.pos[0], self.pos[1] + 15)
        pygame.draw.polygon(self.win, self.color, (
            (self.pos[0] - self.size[0] / 2, self.pos[1]), (self.pos[0] + self.size[0] / 2, self.pos[1]),
            (self.pos[0] + self.size[0] / 2, self.pos[1] + 7), main_point,
            (self.pos[0] - self.size[0] / 2, self.pos[1] + 7)))

        pygame.draw.line(self.win, self.color, main_point, (main_point[0], main_point[1] + self.size[1]), width=3)

    def set_pos_x(self, x):
        self.pos = (x, self.pos[1])

    def is_hovered(self, mouse_pos):
        if self.pos[0] - self.size[0] / 2 - 3 <= mouse_pos[0] <= self.pos[0] + self.size[0] / 2 + 3 and self.pos[1] <= \
                mouse_pos[1] <= self.pos[1] + 18:
            return True
        return False
