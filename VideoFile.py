import os
import time

import cv2
import pygame


class VideoFile:
    def __init__(self, path):
        self.path = path
        self.title = os.path.basename(path)

        self.mid_frame = None

        self.length = None

        self.fps = None

        self.is_loaded = False
        self.video_object = None

        self.video = []

        self.getFileInfo()

    def getFileInfo(self):
        vidcap = cv2.VideoCapture(self.path)
        amount_of_frames = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
        vidcap.set(cv2.CAP_PROP_POS_FRAMES, amount_of_frames//2 - 1)
        success, image = vidcap.read()

        self.mid_frame = pygame.image.frombuffer(image.tostring(), image.shape[1::-1], "BGR").convert()
        self.fps = vidcap.get(cv2.CAP_PROP_FPS)
        self.length = amount_of_frames

    def load(self):
        self.video_object = cv2.VideoCapture(self.path)
        resolution = (1280, 720)
        self.video = []
        while self.video_object.isOpened():
            frame_exists, frame = self.video_object.read()
            if frame_exists:
                frame = cv2.resize(frame,resolution,fx=0,fy=0, interpolation = cv2.INTER_CUBIC)
                self.video.append(pygame.image.frombuffer(frame.tostring(), frame.shape[1::-1], "BGR").convert())
            else:
                break
        self.video_object.release()
        self.is_loaded = True

    def get_frame(self, frame_index):
        image = self.video[frame_index]
        return image