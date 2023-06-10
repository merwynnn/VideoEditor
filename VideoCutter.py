import pygame

from Components import Button, get_hovered_color
from Timeline import Handle, Video

title_font = pygame.font.SysFont('arial', 25)
small_font = pygame.font.SysFont('arial', 15)


class VideoCutter:
    BACKGROUND_COLOR = (18, 18, 18)

    def __init__(self, win, pos, size, videoEditor, video_file, cut_template):
        self.win = win
        self.pos = pos
        self.size = size
        self.videoEditor = videoEditor
        self.video_file = video_file
        self.cut_template = cut_template

        self.cut_frame_start = 0

        self.done_btn = DoneBtn(self.videoEditor, self.win,
                                (self.pos[0] + self.size[0] // 2, self.pos[1] + self.size[1] - 40), (100, 40))

        self.main_row_size = (self.size[0] - 30, 50)
        self.main_row_pos = (self.done_btn.pos[0] - self.size[0] // 2 + 15,
                             self.done_btn.pos[1] - self.done_btn.size[1] // 2 - self.main_row_size[1] - 20)

        self.timeline_surface = pygame.Surface(self.main_row_size)

        self.zoom = 1
        self.zoom_factor = self.video_file.length

        self.handle = Handle(self.win, (self.main_row_pos[0], self.main_row_pos[1] + self.main_row_size[1] + 5), (self.main_row_size[0], 6), (0, self.zoom_factor), self.video_file.length, self.zoom, self.zoom_factor)

        self._is_moving_cut = False
        self._start_frame = None
        self.stored_start = 0

        self.cut_template_length = self.cut_template.get_length_with_fps(
            self.cut_template.end - self.cut_template.start, self.videoEditor.project_data.fps, self.video_file.fps)


        self.cut_position = (0, 0)

    def frame(self, events, mouse_pos):
        rect = pygame.Rect(self.pos, self.size)
        pygame.draw.rect(self.win, self.BACKGROUND_COLOR, rect, border_radius=10)

        self.handle.hovered = self.handle.is_hovered(mouse_pos)

        t = title_font.render("Video Cutter", True, (255, 255, 255))
        title_pos = (self.win.get_width() // 2, self.pos[1] + 5)
        self.win.blit(t, (title_pos[0] - t.get_rect().width / 2, title_pos[1]))

        s = self.frame_to_pos(self.cut_frame_start)
        e = self.frame_to_pos(self.cut_frame_start + self.cut_template_length)
        self.cut_position = (s, e)

        is_cut_hovered = self.is_cut_hovered(mouse_pos)

        timeline_hovered = self.is_timeline_hovered(mouse_pos)
        keys = pygame.key.get_pressed()
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if timeline_hovered:
                    if event.button == 4:
                        if self.zoom * 0.9 > 0.01:
                            self.zoom *= 0.9
                    elif event.button == 5:
                        if self.zoom * 1.1 < 1:
                            self.zoom *= 1.1
                    if event.button == 1:
                        if is_cut_hovered:
                            self._is_moving_cut = True
                            self._start_frame = self.x_to_frame(mouse_pos[0])
                            self.stored_start = self.cut_frame_start
            if event.type == pygame.MOUSEBUTTONUP:
                self._is_moving_cut = False

            if event.type == pygame.KEYDOWN:
                if keys[pygame.K_RIGHT]:
                    if self.cut_frame_start+self.cut_template_length < self.video_file.length:
                        self.cut_frame_start += 1
                if keys[pygame.K_LEFT]:
                    if self.cut_frame_start > 0:
                        self.cut_frame_start -= 1

        if self._is_moving_cut:
            mouse_pos_frame = self.x_to_frame(mouse_pos[0])
            new_start = self.stored_start + (mouse_pos_frame-self._start_frame)
            self.cut_frame_start = new_start

        self.handle.zoom = self.zoom
        self.handle.frame(events, mouse_pos)

        self.timeline_surface.fill(self.BACKGROUND_COLOR)

        s = self.frame_to_pos(0)-self.main_row_pos[0]
        e = self.frame_to_pos(self.video_file.length)-self.main_row_pos[0]
        size = e-s
        video_size = self.video_file.mid_frame.get_size()
        w = (video_size[0] * self.main_row_size[1]) // video_size[1]
        nb = int(size // w)
        if nb > 0:
            for i in range(nb):
                self.timeline_surface.blit(pygame.transform.scale(self.video_file.mid_frame, (w, self.main_row_size[1])),
                              (s+i * w, 0))
            if size % w - size != 0:
                self.timeline_surface.blit(
                    pygame.transform.scale(self.video_file.mid_frame,
                                           (size % w, self.main_row_size[1])),
                    (s+nb * w, 0))

        # Draw clip outline
        s = self.frame_to_pos(self.cut_frame_start)-self.main_row_pos[0]
        e = self.frame_to_pos(self.cut_frame_start + self.cut_template_length)-self.main_row_pos[0]
        rect = pygame.Rect((s, 0), (e - s, self.main_row_size[1]))
        pygame.draw.rect(self.timeline_surface, (245, 217, 37), rect, width=3)

        # draw used part of video
        for videoObject in self.video_file.videoObjects:
            s = self.frame_to_pos(videoObject.video_start) - self.main_row_pos[0]
            e = self.frame_to_pos(videoObject.video_end) - self.main_row_pos[0]
            rect = pygame.Rect((s, 0), (e - s, self.main_row_size[1]))
            pygame.draw.rect(self.timeline_surface, (0, 255, 0), rect, width=2)

        self.win.blit(self.timeline_surface, self.main_row_pos)

        offset = 20
        preview_height = (self.main_row_pos[1]-(title_pos[1]+t.get_height()))-8*offset
        preview_width = self.video_file.mid_frame.get_width()*preview_height//self.video_file.mid_frame.get_height()
        self.win.blit(pygame.transform.scale(self.video_file.get_frame(self.cut_frame_start), (preview_width, preview_height)), (self.pos[0]+self.size[0]//2-preview_width-offset, title_pos[1]+t.get_height()+offset*4))
        self.win.blit(pygame.transform.scale(self.video_file.get_frame(self.cut_frame_start+self.cut_template_length), (preview_width, preview_height)), (self.pos[0]+self.size[0]//2+offset, title_pos[1]+t.get_height()+offset*4))

        self.done_btn.frame(events, mouse_pos)

    def frame_to_pos(self, frame):
        s = int(self.handle.view_limits[0])
        e = int(self.handle.view_limits[1]) - s
        t = frame - s

        return (self.main_row_size[0] * t) / e + self.main_row_pos[0]
        #return (frame * self.main_row_size[0]) // self.video_file.length

    def is_timeline_hovered(self, mouse_pos):
        if self.main_row_pos[0] <= mouse_pos[0] <= self.main_row_pos[0] + self.main_row_size[0] and self.main_row_pos[1] <= mouse_pos[1] <= self.main_row_pos[1] + \
                self.main_row_size[1]:
            return True
        return False

    def is_cut_hovered(self, mouse_pos):
        if self.cut_position[0] <= mouse_pos[0] <=  self.cut_position[0] + self.cut_template_length and self.main_row_pos[1] <= mouse_pos[1] <= self.main_row_pos[1] + \
                self.main_row_size[1]:
            return True
        return False

    def get_cutted_video(self):
        return Video(self.videoEditor.timeline, self.video_file, row=self.cut_template.row, start=self.cut_template.start, end=self.cut_template.end, video_start=self.cut_frame_start)

    def x_to_frame(self, x):
        e = self.handle.view_limits[1] - self.handle.view_limits[0]
        return int(((x - self.main_row_pos[0]) * e / self.main_row_size[0]) + self.handle.view_limits[0])


class DoneBtn(Button):
    BACKGROUND_COLOR = (48, 48, 48)

    def __init__(self, videoEditor, display, pos, size):
        super().__init__(display, pos, size, self.done)
        self.center = True

        self.videoEditor = videoEditor

    def done(self):
        self.videoEditor.on_video_cutter_done()

    def blit(self):
        rect = pygame.Rect((self.pos[0] - self.size[0] / 2, self.pos[1] - self.size[1] / 2), self.size)
        pygame.draw.rect(self.display, self.BACKGROUND_COLOR, rect, 0, 1)
        pygame.draw.rect(self.display, (255, 255, 255), rect, 1, 1)

        name = small_font.render("Done", True, (255, 255, 255))

        self.display.blit(name, (
            self.pos[0] - name.get_rect().width / 2,
            self.pos[1] - name.get_rect().height / 2))

    def blit_hovered(self):
        rect = pygame.Rect((self.pos[0] - self.size[0] / 2, self.pos[1] - self.size[1] / 2), self.size)
        pygame.draw.rect(self.display, get_hovered_color(self.BACKGROUND_COLOR), rect, 0, 1)
        pygame.draw.rect(self.display, (255, 255, 255), rect, 1, 1)

        name = small_font.render("Done", True, (255, 255, 255))

        self.display.blit(name, (
            self.pos[0] - name.get_rect().width / 2,
            self.pos[1] - name.get_rect().height / 2))
