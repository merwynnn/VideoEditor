from itertools import chain

from VideoFile import VideoFile


class ProjectData:
    def __init__(self, videoEditor):
        self.videoEditor = videoEditor

        self.video_paths = []
        self.videos = []

        self.rows_size = [1, 0.5]
        self.row_factor = 100
        self.rows = [[] for _ in range(len(self.rows_size))]

        self.main_song = None
        self.length = None

        self.fps = 30

    def __getstate__(self):
        state = self.__dict__.copy()
        # Don't pickle display
        try:
            del state["videoEditor"]
            del state["videos"]
        except KeyError:
            pass
        return state

    def __setstate__(self, state):
        """ Called on load data from file (unpickle) """
        self.__dict__.update(state)
        self.videos = []

    def load(self, videoEditor):
        self.videoEditor = videoEditor
        for video in self.video_paths:
            video_file = VideoFile(video, self.videoEditor)
            self.videos.append(video_file)
            for video_object in list(chain.from_iterable(self.rows)):
                if video_object.video_path == video:
                    video_object.video_file = video_file
                    video_file.videoObjects.append(video_object)
                    break