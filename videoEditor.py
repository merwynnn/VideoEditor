import sys

import pygame

pygame.font.init()

from Previewer import Previewer
from FileBrowser import FileBrowser
from ProjectData import ProjectData
from VideoFile import VideoFile
from Timeline import Timeline
import tkinter as tk
from tkinter.filedialog import askopenfilenames, askopenfilename
from mutagen.mp3 import MP3

tk.Tk().withdraw() # part of the import if you are not using other tkinter functions


class VideoEditor:
    BACKGROUND_COLOR = (18, 18, 18)

    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
        pygame.display.set_caption('VideoEditor')

        self.size = self.window.get_size()

        self.project_data = ProjectData()

        self.get_main_song()        # Asks the user for a song

        self.video_size = (1920, 1080)
        self.previewer = Previewer(self.window, (self.size[0]*0.25, 0), (self.size[0]*0.50, 1080*(self.size[0]*0.50)/1920))

        self.timeline = Timeline(self.window, (5, self.previewer.size[1]), (self.size[0]-5, self.size[1]-self.previewer.size[1]), self)

        self.file_browser = FileBrowser(self.window, (0, 0), (self.size[0]*0.25, self.previewer.size[1]), self)

        self.start()

    def start(self):
        clock = pygame.time.Clock()

        while True:
            self.window.fill(self.BACKGROUND_COLOR)

            events = pygame.event.get()
            pos = pygame.mouse.get_pos()

            for event in events:
                if event.type == pygame.QUIT:
                    sys.exit()

            self.previewer.frame(events, pos)

            self.timeline.frame(events, pos)

            self.file_browser.frame(events, pos)
            clock.tick()
            fps = clock.get_fps()
            #print(int(fps))
            pygame.display.update()

    def add_video(self):
        files = askopenfilenames(title='Choose a media', filetypes=[("Media files", ".mp4")])
        for video in files:
            new_video = VideoFile(video)
            self.project_data.videos.append(new_video)

        self.file_browser.update()

    def get_main_song(self):
        file = askopenfilename(title='Choose a song', filetypes=[("Song files", ".mp3")])
        self.project_data.main_song = file
        audio = MP3(self.project_data.main_song)

        self.project_data.length = audio.info.length