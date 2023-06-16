import cv2
import numpy as np
import pygame


class Transition:
    def __init__(self, win, video_start, video_end, duration, name="Transition"):
        self.win = win

        self.name = name
        self.video_start = video_start
        self.video_end = video_end

        self.duration = duration

    def frame(self, events, mouse_pos):
        row_pos_y,row_size_y = self.video_start.timeline.get_row_pos_size(self.video_start.row)
        pos = (self.video_start.timeline.frame_to_pos(self.get_start_frame_index()), row_pos_y+row_size_y//3)
        size = (self.video_start.timeline.frame_to_pos(self.get_end_frame_index())-pos[0], row_size_y//3)
        rect = pygame.Rect(pos, size)
        pygame.draw.rect(self.win, (20, 20, 20), rect)

    def mix(self, frame_start, frame_end, delta_time):
        pass

    def get_frame(self, frame_index):
        delta_time = frame_index - self.get_start_frame_index()
        frame_start = self.video_start.get_frame_at_pos(frame_index, pg_image=False, ignore_transition=True)
        frame_end = self.video_end.get_frame_at_pos(frame_index, pg_image=False, ignore_transition=True)

        image =self.mix(frame_start, frame_end, delta_time)
        return image

    def get_high_res_frame(self, frame_index):
        delta_time = frame_index - self.get_start_frame_index()
        frame_start = self.video_start.get_high_res_frame_at_pos(frame_index)
        frame_end = self.video_end.get_high_res_frame_at_pos(frame_index)

        return self.mix(frame_start, frame_end, delta_time)

    def get_start_frame_index(self):
        return self.video_start.end - self.duration // 2

    def get_end_frame_index(self):
        return self.video_end.start + self.duration // 2


class FadeTransition(Transition):
    def __init__(self, win, video_start, video_end, duration=30):
        super().__init__(win, video_start, video_end, duration, "Fade")

    def mix(self, frame_video_1, frame_video_2, delta_time):
        f1_opacity = (self.duration - delta_time) / self.duration
        f2_opacity = 1 - f1_opacity
        image = cv2.addWeighted(frame_video_1, f1_opacity, frame_video_2, f2_opacity, 0)

        return image

class DipToBlackTransition(Transition):
    def __init__(self, win, video_start, video_end, duration=60):
        super().__init__(win, video_start, video_end, duration, "DipToBlack")

    def mix(self, frame_video_1, frame_video_2, delta_time):
        transition_duration = self.duration / 2  # Divide the transition time equally between the two fades
        black_frame = np.zeros(frame_video_1.shape, dtype=np.uint8)  # Create a black frame

        if delta_time <= transition_duration:
            f1_opacity = (transition_duration - delta_time) / transition_duration
            black_frame_opacity = 1 - f1_opacity
            image = cv2.addWeighted(frame_video_1, f1_opacity, black_frame, black_frame_opacity, 0)

        else:
            black_frame_opacity = (transition_duration - (delta_time-transition_duration)) / transition_duration
            f2_opacity = 1-black_frame_opacity
            image = cv2.addWeighted(black_frame, black_frame_opacity, frame_video_2, f2_opacity, 0)
        return image

class LeftToRightTransition(Transition):
    def __init__(self, win, video_start, video_end, duration=60):
        super().__init__(win, video_start, video_end, duration, "LeftToRightTransition")

    def mix(self, frame_video_1, frame_video_2, delta_time):
        f1_opacity = 1 - (self.duration - delta_time) / self.duration

        f2_opacity = 1 - f1_opacity
        image = cv2.addWeighted(frame_video_1, f1_opacity, frame_video_2, f2_opacity, 0)

        return image






