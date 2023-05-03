import random
import sys
import time

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

        self.rows_size = [1, 0.5]
        self.row_factor = 100
        self.rows = [[] for _ in range(len(self.rows_size))]

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

        self.selected_timeline_objects = []

        self.video_object_at_cursor = None

        self._is_cursor_moving = False
        self._is_moving_objects = False
        self._start_frame = None

        self._current_ghost_object = None

        self._start_play_frame = 0

    def frame(self, events, mouse_pos):
        pygame.draw.rect(self.win, self.BACKGROUND_COLOR,
                         pygame.Rect((self.pos[0] - 5, self.pos[1]), (self.size[0] + 10, self.size[1])))

        self.handle.hovered = self.handle.is_hovered(mouse_pos)
        hovered = self.is_hovered(mouse_pos)

        if self.videoEditor.is_playing:
            self.cursor_pos = (pygame.mixer.music.get_pos() / 1000) * self.videoEditor.project_data.fps + self._start_play_frame
            self.load_at_cursor_position()

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
                        if self.is_top_hovered(mouse_pos):
                            if self.cursor.is_hovered(mouse_pos):
                                self._is_cursor_moving = True
                            else:
                                self.cursor_pos = self.x_to_frame(mouse_pos[0])
                                self.videoEditor.previewer.has_cursor_moved = True
                                self._start_play_frame = self.cursor_pos
                                self.load_at_cursor_position()
                        elif not self.handle.hovered:
                            obj = self.get_hovered_timeline_object(mouse_pos)
                            if obj:
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
                self._is_cursor_moving = False
                self._is_moving_objects = False

        if self._is_cursor_moving:
            self.cursor_pos = self.x_to_frame(mouse_pos[0])
            self.videoEditor.previewer.has_cursor_moved = True
            self._start_play_frame = self.cursor_pos
            self.load_at_cursor_position()

        if self._is_moving_objects:
            for t_object in self.selected_timeline_objects:
                mouse_pos_frame = self.x_to_frame(mouse_pos[0])
                new_start = t_object.stored_start + (mouse_pos_frame-self._start_frame)
                t_object.end = new_start + (t_object.end-t_object.start)
                t_object.start = new_start

        self.handle.zoom = self.zoom
        self.handle.frame(events, mouse_pos)

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
                timeline_object.frame(events, mouse_pos, selected=True if timeline_object in self.selected_timeline_objects else False)

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
        for e in self.rows_size[:row]:
            y += e * self.row_factor
        return self.pos[1] + self.top_bar_height + y, self.rows_size[row] * self.row_factor

    def add_cut_template(self, f_start, f_end):
        t = BlankObject(self, 0, f_start, f_end)
        self.add_object_to_timeline(t)

    def add_video(self, f_start, video_file, row=0):
        v = Video(self, video_file, row, start = f_start)
        self.add_object_to_timeline(v)
        self.load_at_cursor_position()

    def add_object_to_timeline(self, t_object):
        self.timeline_objects.append(t_object)
        l = len(self.rows[t_object.row])
        if l > 0:
            i = 0
            while t_object.start > self.rows[t_object.row][i].end:
                i += 1
                if l-1 < i:
                    break
            self.rows[t_object.row].insert(i, t_object)
        else:
            self.rows[t_object.row].append(t_object)

    def remove_object_from_timeline(self, t_object):
        self.rows[t_object.row].remove(t_object)
        self.timeline_objects.remove(t_object)

    def get_video_at_position(self, frame):
        videos = self.rows[0]
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
        self.video_object_at_cursor.video_file.load_at_frame(self.video_object_at_cursor.get_relative_frame_index(self.cursor_pos))

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

        self.stored_start = None    # used when moving object

    def frame(self, events, mouse_pos, selected = False):
        s = self.frame_to_pos(self.start)
        e = self.frame_to_pos(self.end)
        row_y, row_height = self.timeline.get_row_pos_size(self.row)
        pos = (s, row_y)
        size = (e - s, row_height)
        rect = pygame.Rect(pos, size)
        pygame.draw.rect(self.timeline.win, self.color, rect)

        if selected:
            # On select
            offset = 2
            rect = pygame.Rect((pos[0]-offset, pos[1]-offset), (size[0]+offset*2, size[1]+offset*2))
            pygame.draw.rect(self.timeline.win, self.selected_color, rect, width=2)

        self.hovered = True if pos[0] <= mouse_pos[0] <= pos[0] + size[0] and pos[1] <= mouse_pos[1] <= pos[1] + size[1] else False

        self.top_frame(events, mouse_pos, pos, size)

    def time_to_pos(self, time):
        e = (self.timeline.handle.view_limits[1] - self.timeline.handle.view_limits[0]) / self.timeline.VideoEditor.project_data.fps
        t = time - (self.timeline.handle.view_limits[0] / self.timeline.videoEditor.project_data.fps)

        return (self.timeline.size[0] * t) / e + self.timeline.pos[0]

    def frame_to_pos(self, frame):
        s = int(self.timeline.handle.view_limits[0])
        e = int(self.timeline.handle.view_limits[1]) - s
        t = frame - s

        return (self.timeline.size[0] * t) / e + self.timeline.pos[0]

    def x_to_frame(self, x):
        e = self.timeline.handle.view_limits[1] - self.timeline.handle.view_limits[0]
        return int(((x - self.timeline.pos[0]) * e / self.timeline.size[0]) + self.timeline.handle.view_limits[0])

    def top_frame(self, events, mouse_pos, row_pos, row_size):
        pass

    def get_length_with_fps(self, original_length, original_fps, targeted_fps):
        return (targeted_fps * original_length) // original_fps



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
        end = start + self.get_length_with_fps(video_file.length-video_start, video_file.fps, timeline.videoEditor.project_data.fps)

        super().__init__(timeline, row, start, end,
                         (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

        self.video_file = video_file

        self.video_start = None
        self.video_end = None
        self.calculate_video_start_end(video_start, video_end)
        print(self.video_start, self.video_end)

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
                f2 = self.get_absolute_frame_index(frame_index+n)
                pos1 = (self.frame_to_pos(f1), row_pos[1])
                pos2 = (self.frame_to_pos(f2), row_pos[1])
                pygame.draw.line(self.timeline.win, (255, 0, 0), pos1, pos2)

    def get_relative_frame_index(self, abs_frame):
        relative_pos = abs_frame - self.start
        return self.video_start + int((relative_pos * (self.video_end-self.video_start)) // (self.end - self.start))

    def get_absolute_frame_index(self, rel_frame):
        absolute_pos = int(((rel_frame-self.video_start)*(self.end - self.start))/(self.video_end-self.video_start))
        return absolute_pos + self.start

    def get_frame_at_pos(self, pos):
        frame_with_fps = self.get_relative_frame_index(pos)

        frame = self.video_file.get_frame(frame_with_fps)

        return frame

    def calculate_video_start_end(self, video_start=None, video_end=None):
        if video_start is not None:
            self.video_start = video_start
            self.video_end = self.video_start + self.get_length_with_fps(self.end - self.start, self.timeline.videoEditor.project_data.fps,
                                                                         self.video_file.fps)
        elif video_end is not None:
            self.video_start = video_end - self.get_length_with_fps(self.end - self.start, self.timeline.videoEditor.project_data.fps, self.video_file.fps)
            self.video_end = video_end

    def cut(self, pos):
        rel_pos = self.get_relative_frame_index(pos)
        t1 = Video(self.timeline, self.video_file, self.row, start=self.start, end=pos, video_start=self.video_start)
        #t1.video_end = rel_pos

        t2 = Video(self.timeline, self.video_file, self.row, start=pos, end=self.end)
        t2.video_start = rel_pos
        t2.video_end = self.video_end

        return t1, t2

class BlankObject(TimelineObject):
    def __init__(self, timeline, row, start, end):
        super().__init__(timeline, row, start, end,
                         (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))


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
                        self._start_handle_pos = self.pos
                        self._start_view_limits = self.view_limits
            if event.type == pygame.MOUSEBUTTONUP:
                self._start_mouse_pos = None
                self._start_handle_pos = None
                self._start_view_limits = None

        l = self.zoom_factor * self.zoom
        mid = (self.view_limits[1] + self.view_limits[0]) / 2
        self.view_limits = (mid - (l / 2), mid + (l / 2))

        if self._start_mouse_pos:  # on drag
            delta = pos[0] - (self._start_mouse_pos[0] - self._start_handle_pos[0])
            delta = (delta * self.length / self.size[0])
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
