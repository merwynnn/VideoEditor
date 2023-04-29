import time

import pygame
import sounddevice as sd
from Timeline import Video, BlankObject
class Previewer:
    def __init__(self, win, pos, size, videoEditor):
        self.win = win
        self.pos = pos
        self.size = size
        self.videoEditor = videoEditor
        pygame.mixer.music.load(self.videoEditor.project_data.main_song)

        self._was_playing = False # if the player was playing last frame
        self.has_cursor_moved = False

        self._needs_update = True   # if something changed

    def frame(self, events, mouse_pos):
        if not self._needs_update and not self.videoEditor.is_playing and not self.has_cursor_moved:
            self._was_playing = False
            pygame.mixer.music.stop()
            return
        self._needs_update = False

        pygame.draw.rect(self.win, (0, 0, 0), pygame.Rect(self.pos, self.size))

        timeline_object = self.videoEditor.timeline.get_video_at_position(self.videoEditor.timeline.cursor_pos)
        if type(timeline_object) == BlankObject:
            color = timeline_object.color
            pygame.draw.rect(self.win, color, pygame.Rect(self.pos, self.size))
        elif type(timeline_object) == Video:
            frame = timeline_object.get_frame_at_pos(self.videoEditor.timeline.cursor_pos)
            self.win.blit(pygame.transform.scale(frame, self.size),  self.pos)

        if self.videoEditor.is_playing:
            if not self._was_playing or self.has_cursor_moved:
                pygame.mixer.music.play(start=self.videoEditor.timeline.cursor_pos/self.videoEditor.project_data.fps)
            self._was_playing = True

        else:
            self._was_playing = False
            pygame.mixer.music.stop()

        if self.has_cursor_moved:
            self.has_cursor_moved = False