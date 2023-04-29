import os
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

    def get_frame(self, frame_index):
        self.video_object.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        success, image = self.video_object.read()
        return pygame.image.frombuffer(image.tostring(), image.shape[1::-1], "BGR").convert()