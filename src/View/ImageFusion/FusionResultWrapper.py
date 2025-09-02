class FusionResultWrapper:
    def __init__(self, images, progress_window):
        self.images = images
        self._progress_window = progress_window

    def update_progress(self, *args, **kwargs):
        if hasattr(self._progress_window, "update_progress"):
            self._progress_window.update_progress(*args, **kwargs)

    def close(self):
        if hasattr(self._progress_window, "close"):
            self._progress_window.close()