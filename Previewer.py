import pygame
import sounddevice as sd

class Previewer:
    def __init__(self, win, pos, size, videoEditor):
        self.win = win
        self.pos = pos
        self.size = size
        self.videoEditor = videoEditor
        pygame.mixer.music.load(self.videoEditor.project_data.main_song)

        self._was_playing = False # if the player was playing last frame
        self.has_cursor_moved = False

    def frame(self, events, mouse_pos):
        pygame.draw.rect(self.win, (0, 0, 0), pygame.Rect(self.pos, self.size))

        if self.videoEditor.is_playing:
            if not self._was_playing or self.has_cursor_moved:
                pygame.mixer.music.play(start=self.videoEditor.timeline.cursor_pos/self.videoEditor.project_data.fps)
            self._was_playing = True

        else:
            self._was_playing = False
            pygame.mixer.music.stop()

        if self.has_cursor_moved:
            self.has_cursor_moved = False