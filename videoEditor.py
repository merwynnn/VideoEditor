import os
import sys
import time
import _pickle as cPickle
from itertools import chain
from multiprocessing import Pool

import cv2
import numpy as np
import pygame
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from tqdm import tqdm

pygame.font.init()
pygame.mixer.init()

from Previewer import Previewer
from FileBrowser import FileBrowser
from ProjectData import ProjectData
from VideoFile import VideoFile
from Timeline import Timeline, Video
from VideoCutter import VideoCutter

import tkinter as tk
from tkinter.filedialog import askopenfilenames, askopenfilename
import soundfile as sf
import psutil
from moviepy.editor import VideoFileClip, AudioFileClip
from PremierePro import Project

import pymiere

tk.Tk().withdraw() # part of the import if you are not using other tkinter functions


class VideoEditor:
    BACKGROUND_COLOR = (18, 18, 18)

    def __init__(self, project_name):
        pygame.init()
        display_info = pygame.display.Info()
        self.width, self.height = display_info.current_w, display_info.current_h
        self.window = pygame.display.set_mode((self.width, self.height-60), pygame.RESIZABLE, 32)
        pygame.display.set_caption('VideoEditor')

        self.project_name = project_name + ".vex"

        self.size = self.window.get_size()

        self.video_size = (1280, 720)

        self.project_data = None
        self.load_data()

        if not self.project_data.main_song:
            self.get_main_song()        # Asks the user for a song

        self.previewer = Previewer(self.window, (self.size[0]*0.25, 0), (self.size[0]*0.50, 1080*(self.size[0]*0.50)/1920), self)

        self.timeline = Timeline(self.window, (5, self.previewer.size[1]), (self.size[0]-5, self.size[1]-self.previewer.size[1]), self)

        self.file_browser = FileBrowser(self.window, (0, 0), (self.size[0]*0.25, self.previewer.size[1]), self)

        self.opened_window = None   # Window opened in front of main window

        self.is_playing = False

        self.available_memory = None
        self.memory_threshold = 100*1024*1024
        self.calculate_available_memory()

        self.max_load_time = 40

        self.pre_load = False

        self.reload_all = False

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
                    elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        self.save()
                    elif event.key == pygame.K_e and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        self.export()
                    elif event.key == pygame.K_p and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        self.export_to_premiere()
            if self.opened_window:
                self.opened_window.frame(events, pos)
            else:
                self.timeline.frame(events, pos)
                self.previewer.frame(events, pos)
                self.file_browser.frame(events, pos)

                self.reload_all = False

            if self.is_playing:
                clock.tick(self.project_data.fps)
            else:
                clock.tick()
            fps = clock.get_fps()
            #print(int(fps))
            pygame.display.update()

    def add_video(self):
        self.is_playing = False
        files = askopenfilenames(title='Choose a media', filetypes=[("Media files", ".mp4")])
        for video in files:
            new_video = VideoFile(video, self)
            self.project_data.videos.append(new_video)
            self.project_data.video_paths.append(new_video.path)

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

    def calculate_available_memory(self):
        self.available_memory = psutil.virtual_memory().available

    def show_video_cutter(self, video_file, cut_template):
        print("show_file")
        self.opened_window = VideoCutter(self.window, (self.width//4, self.height//4), (self.width//2, self.height//2), self, video_file, cut_template)

    def on_video_cutter_done(self):
        self.timeline.remove_object_from_timeline(self.opened_window.cut_template)
        cutted_video = self.opened_window.get_cutted_video()
        self.timeline.add_object_to_timeline(cutted_video)
        cutted_video.video_file.videoObjects.append(cutted_video)
        self.opened_window = None
        self.reload_all = True

    def save(self):
        print("Saving...")
        with open(self.project_name, "wb") as f:
            cPickle.dump(self.project_data, f)

    def load_data(self):
        print("Loading...")
        try:
            with open(self.project_name, "rb") as f:
                data = cPickle.load(f)
        except:
            data = ProjectData(self)
        self.project_data = data
        self.project_data.load(self)

    def export(self):
        print("Exporting...")
        video_name = self.project_name[:-4]+".avi"

        video = cv2.VideoWriter("temp_"+video_name,0,  self.project_data.fps, self.video_size)
        black_image = np.zeros((self.video_size[0], self.video_size[1], 3), dtype = np.uint8)
        for frame_index in tqdm(range(self.project_data.length)):
            videoObject = self.timeline.get_video_at_position(frame_index)
            if videoObject and isinstance(videoObject, Video):
                    frame = videoObject.get_high_res_frame_at_pos(frame_index)
                    video.write(frame)
            else:
                video.write(black_image)

        cv2.destroyAllWindows()
        video.release()
        #videoGenerator = VideoGenerator("temp_"+video_name, self.video_size, self.project_data.fps, self.timeline.get_video_at_position, self.project_data.length)
        #videoGenerator.generate_video()


        video = VideoFileClip("temp_"+video_name)
        audio = AudioFileClip(self.project_data.main_song)

        # Set the audio clip to the video
        video = video.set_audio(audio)

        # Write the video to a new file
        video.write_videofile(video_name, codec="libx264", audio_codec='aac')

        os.remove("temp_"+video_name)


    def export_to_premiere(self):
        print("Exporting to Premiere Pro...")
        project_path = self.project_name[:-4]+".xml"

        # create new empty project
        project = Project(project_path, self.project_name[:-4], self.project_data.fps, self.project_data.length)

        # add the clips to the sequence at different locations
        for videoObject in list(chain.from_iterable(self.project_data.rows)):
            if isinstance(videoObject, Video):
                project.add_video_clip(videoObject.video_path, "Clip", videoObject.start, videoObject.end, videoObject.video_start)

        project.add_audio_clip(self.project_data.main_song, "Main Song")

        project.save()