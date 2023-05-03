import pygame


class VideoCutter:
    BACKGROUND_COLOR = (18, 18, 18)

    def __init__(self, win, pos, size, videoEditor, video_file, cut_template):
        self.win = win
        self.pos = pos
        self.size = size
        self.videoEditor = videoEditor
        self.video_file = video_file
        self.cut_template = cut_template

    def frame(self, events, mouse_pos):
        rect = pygame.Rect(self.pos, self.size)
        pygame.draw.rect(self.win, self.BACKGROUND_COLOR, rect, border_radius=10)