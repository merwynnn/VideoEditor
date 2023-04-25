import os
import cv2
import pygame


class VideoFile:
    def __init__(self, path):
        self.path = path
        self.title = os.path.basename(path)

        self.mid_frame = self.getMidFrame()

    def getMidFrame(self):
        vidcap = cv2.VideoCapture(self.path)
        amount_of_frames = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
        vidcap.set(cv2.CAP_PROP_POS_FRAMES, amount_of_frames//2 - 1)
        success, image = vidcap.read()

        return pygame.image.frombuffer(image.tostring(), image.shape[1::-1], "BGR")