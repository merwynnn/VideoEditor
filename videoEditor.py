import sys

import numpy as np
import pygame

pygame.font.init()
pygame.mixer.init()

from Previewer import Previewer
from FileBrowser import FileBrowser
from ProjectData import ProjectData
from VideoFile import VideoFile
from Timeline import Timeline
import tkinter as tk
from tkinter.filedialog import askopenfilenames, askopenfilename
from mutagen.mp3 import MP3
import soundfile as sf


tk.Tk().withdraw() # part of the import if you are not using other tkinter functions


class VideoEditor:
    BACKGROUND_COLOR = (18, 18, 18)

    def __init__(self):
        pygame.init()
        display_info = pygame.display.Info()
        self.width, self.height = display_info.current_w, display_info.current_h
        self.window = pygame.display.set_mode((self.width, self.height-60), pygame.RESIZABLE, 32)
        pygame.display.set_caption('VideoEditor')

        self.size = self.window.get_size()

        self.project_data = ProjectData()

        self.get_main_song()        # Asks the user for a song

        self.video_size = (1920, 1080)
        self.previewer = Previewer(self.window, (self.size[0]*0.25, 0), (self.size[0]*0.50, 1080*(self.size[0]*0.50)/1920), self)

        self.timeline = Timeline(self.window, (5, self.previewer.size[1]), (self.size[0]-5, self.size[1]-self.previewer.size[1]), self)

        self.file_browser = FileBrowser(self.window, (0, 0), (self.size[0]*0.25, self.previewer.size[1]), self)

        self.is_playing = False

        self.create_cuts_template(self.project_data.main_song)

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
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.is_playing = not self.is_playing

            self.previewer.frame(events, pos)

            self.timeline.frame(events, pos)

            self.file_browser.frame(events, pos)
            if self.is_playing:
                clock.tick(self.project_data.fps)
            else:
                clock.tick()
            fps = clock.get_fps()
            print(int(fps))
            pygame.display.update()

    def add_video(self):
        self.is_playing = False
        files = askopenfilenames(title='Choose a media', filetypes=[("Media files", ".mp4")])
        for video in files:
            new_video = VideoFile(video)
            self.project_data.videos.append(new_video)

        self.file_browser.update()

    def get_main_song(self):
        self.is_playing = False
        file = askopenfilename(title='Choose a song', filetypes=[("Song files", ".mp3")])
        self.project_data.main_song = file
        audio = MP3(self.project_data.main_song)

        self.project_data.length = int(audio.info.length * self.project_data.fps)

    def create_cuts_template(self, audio_file):
        onset_times = self.get_onset_times(audio_file)

        last_cut = 0
        for cut in onset_times:
            cur_cut = int(cut*self.project_data.fps)
            self.timeline.add_cut_template(last_cut, cur_cut)
            last_cut = cur_cut

    def get_onset_times(self, file_path):
        audio_file = sf.SoundFile(file_path)
        samples = audio_file.read()
        if len(samples.shape) > 1:
            # Average the two channels to get a mono signal
            samples = np.mean(samples, axis=1)

        parts = []
        for i in range(len(samples)//audio_file.samplerate):
            if (i+1)*audio_file.samplerate > len(samples):
                parts.append(samples[i * audio_file.samplerate:])
                break
            else:
                parts.append(samples[i*audio_file.samplerate:(i+1)*audio_file.samplerate])

        for part in parts:
            m = np.mean(part)
            print(m)
