import os
import time

import cv2
import pygame
import sys

class VideoFile:
    def __init__(self, path, videoEditor):
        self.path = path
        self.videoEditor = videoEditor

        self.title = os.path.basename(path)

        self.mid_frame = None

        self.length = None

        self.fps = None

        self.video_object = cv2.VideoCapture(self.path)
        self.video_object.set(cv2.CAP_PROP_BUFFERSIZE, 2)

        self.video = {}     # {first_loaded_frame_index: [frame, frame+1, frame+2, ...], }       ____#######____##################____
        self.nb_loaded_frames = 0

        self.should_load = True
        self.is_loading = False

        self.preview_resolution = (1280, 720)
        self.high_resolution = self.videoEditor.video_size
        self.frame_size_bytes = None

        self.videoObjects = []

        self.getFileInfo()

    def getFileInfo(self):
        vidcap = cv2.VideoCapture(self.path)
        amount_of_frames = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
        vidcap.set(cv2.CAP_PROP_POS_FRAMES, amount_of_frames//2 - 1)
        success, image = vidcap.read()

        self.mid_frame = pygame.image.frombuffer(image.tostring(), image.shape[1::-1], "BGR").convert()

        f = cv2.resize(image, self.preview_resolution,fx=0,fy=0, interpolation = cv2.INTER_CUBIC)

        self.fps = vidcap.get(cv2.CAP_PROP_FPS)
        self.length = amount_of_frames

    def load_at_frame(self, frame_index):
        self.should_load = False
        while self.is_loading:  # wait for other threads to stop
            pass

        self.is_loading = True
        self.should_load = True

        frame = frame_index

        frames = self.video.get(frame_index)
        if frames:
            frame = frame_index + len(frames)
        else:
            self.video[frame_index] = []

        keys = tuple(self.video.keys())
        k_before = [key for key in keys if key < frame_index]

        if len(keys) > 0:
            for key in k_before:
                if key+len(self.video[key]) > frame:
                    i = frame_index-key # index of frame_index in key
                    e = self.video[key][i:]
                    self.video[frame_index] = e
                    frame=key+len(self.video[key])-1
                    self.video[key] = self.video[key][:i]

        k_after = [key for key in keys if key > frame_index]

        self.videoEditor.calculate_available_memory()
        nb_frame_before_memory_update = 5
        memory_update_cooldown = nb_frame_before_memory_update

        self.video_object.set(cv2.CAP_PROP_POS_FRAMES, frame)

        while self.video_object.isOpened() and self.should_load:
            if frame in k_after:
                k_after.remove(frame)
                self.video[frame_index] += self.video[frame]
                del self.video[frame]
                frame = frame_index+len(self.video[frame_index])+1
                self.video_object.set(cv2.CAP_PROP_POS_FRAMES, frame)

            frame_exists, f = self.video_object.read()
            if frame_exists:
                f = cv2.resize(f,self.preview_resolution,fx=0,fy=0, interpolation = cv2.INTER_CUBIC)
                f = pygame.image.frombuffer(f.tostring(), f.shape[1::-1], "BGR").convert()
                self.video[frame_index].append(f)
                self.nb_loaded_frames += 1
            else:
                break
            memory_update_cooldown -= 1
            if memory_update_cooldown == 0:
                memory_update_cooldown = nb_frame_before_memory_update
                self.videoEditor.calculate_available_memory()
            if self.videoEditor.available_memory <= self.videoEditor.memory_threshold or self.nb_loaded_frames > self.videoEditor.max_load_time*self.fps:
                # Unload useless frame

                c_key = 10*100
                check = False
                for key in k_before:
                    if key < c_key:
                        c_key = key
                        check = True
                if check:
                    if self.video.get(c_key):
                        if c_key+1 != frame_index:
                            self.video[c_key + 1] = self.video[c_key][1:]
                            k_before.append(c_key+1)
                        k_before.remove(c_key)
                        del self.video[c_key]

                        self.nb_loaded_frames -= 1
                else:
                    c_key = 0
                    check = False
                    for key in k_after:
                        if key > c_key:
                            c_key = key
                            check = True
                    if check:
                        self.video[c_key] = self.video[c_key][:-1]
                        if len(self.video[c_key]) == 0:
                            del self.video[c_key]
                            k_after.remove(c_key)
                            self.nb_loaded_frames -= 1
                    else:
                        break

            frame += 1

        self.is_loading = False

    def get_frame(self, frame_index, pg_image=True):
        if self.videoEditor.pre_load:
            c_key = 0
            check=False
            for key in self.video.keys():
                if frame_index >= key > c_key:
                    c_key = key
                    check = True
            if check:
                if len(self.video[c_key]) - 1 >= frame_index - c_key:
                    image = self.video[c_key][frame_index - c_key]
                    return image
        else:
            self.video_object.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            frame_exists, f = self.video_object.read()
            if frame_exists:
                f = cv2.resize(f,self.preview_resolution,fx=0,fy=0, interpolation = cv2.INTER_CUBIC)
                if pg_image:
                    f = pygame.image.frombuffer(f.tostring(), f.shape[1::-1], "BGR").convert()
                return f
        return None

    def get_high_res_frame(self, frame_index):
        self.video_object.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        frame_exists, f = self.video_object.read()
        if frame_exists:
            f = cv2.resize(f, self.high_resolution, fx=0, fy=0, interpolation=cv2.INTER_CUBIC)
            return f
