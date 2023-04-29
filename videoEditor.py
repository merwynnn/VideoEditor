import sys
import time

import numpy as np
import pygame
from scipy.signal import find_peaks

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

        self.start()

    def start(self):
        clock = pygame.time.Clock()
        self.window.fill(self.BACKGROUND_COLOR)

        while True:
            events = pygame.event.get()
            pos = pygame.mouse.get_pos()

            for event in events:
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.is_playing = not self.is_playing
            t = time.time()
            self.previewer.frame(events, pos)
            t1 = time.time()
            self.timeline.frame(events, pos)
            t2 = time.time()
            self.file_browser.frame(events, pos)
            t3=time.time()

            print("-----------")
            print("previewer: ", t1-t)

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
        file = askopenfilename(title='Choose a song', filetypes=[("Song files", ".mp3 .wav")])
        self.project_data.main_song = file
        audio_file = sf.SoundFile(self.project_data.main_song)

        self.project_data.length = int((audio_file.frames / audio_file.samplerate) * self.project_data.fps)

    def create_cuts_template(self, audio_file):
        onset_times = self.get_onset_times1(audio_file)

        last_cut = 0
        for cut in onset_times:
            cur_cut = cut
            print(last_cut, cur_cut)
            self.timeline.add_cut_template(last_cut, cur_cut)
            last_cut = cur_cut

    def get_onset_times(self, file_path):
        audio_file = sf.SoundFile(file_path)
        samples = audio_file.read()
        if len(samples.shape) > 1:
            # Average the two channels to get a mono signal
            samples = np.mean(samples, axis=1)

        d = 0.5
        parts_mean = []
        for i in range(int(len(samples) // (audio_file.samplerate * d))):
            if (i + 1) * (audio_file.samplerate * d) > len(samples):
                parts_mean.append(np.mean(np.array(samples[int(i * audio_file.samplerate * d):])))
                break
            else:
                parts_mean.append(
                    np.mean(np.array(samples[int(i * audio_file.samplerate * d):int((i + 1) * audio_file.samplerate * d)])))

        peaks2, _ = find_peaks(parts_mean, width=1, distance=3)
        times = []
        for peak in peaks2:
            times.append(peak*d)
        audio_file.close()
        return times
