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
        pos = (self.video_start.timeline.frame_to_pos(self.video_start.start), row_pos_y)

        position = (pos[0], pos[1]+row_size_y//2)
        pos = (self.video_start.timeline.frame_to_pos(self.get_start_frame_index()), position[1]-row_size_y//4)
        rect = pygame.Rect(pos, (self.video_start.timeline.frame_to_pos(self.get_end_frame_index())-pos[0], row_size_y//2))
        pygame.draw.rect(self.win, (20, 20, 20), rect)

    def mix(self, frame_start, frame_end, delta_time):
        pass

    def get_frame(self, frame_index):
        delta_time = frame_index - self.get_start_frame_index()
        frame_start = self.video_start.get_frame_at_pos(frame_index, pg_image=False)
        frame_end = self.video_end.get_frame_at_pos(frame_index, pg_image=False)

        return self.mix(frame_start, frame_end, delta_time)

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

    def mix(self, frame_start, frame_end, delta_time):
        f1_opacity = (self.duration-delta_time)/self.duration
        f2_opacity = 1-f1_opacity

        image = frame_start*f1_opacity+frame_end*f2_opacity

        return image

