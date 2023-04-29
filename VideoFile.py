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
        self.video = []
        while self.video_object.isOpened():
            frame_exists, frame = self.video_object.read()
            if frame_exists:
                self.video.append(frame)
            else:
                break
        self.video_object.release()
        self.is_loaded = True

    def get_frame(self, frame_index):
        image = self.video[frame_index]
        t2 = time.time()
        image = pygame.image.frombuffer(image.tostring(), image.shape[1::-1], "BGR").convert()
        t3 = time.time()
        print("pygame: ", t3-t2)
        return image