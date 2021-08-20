import math
from src.Model.LiveWireAlgorithm.Dijkstra import shortestPath

class LiveWireSegmentation(object):
    def __init__(self, image=None, smooth_image=False, threshold_gradient_image=False):
        super(LiveWireSegmentation, self).__init__()

        # init internal containers

        # container for input image
        self._image = None

        # container for the gradient image
        self.edges = None

        # stores the image as an undirected graph for shortest path search
        self.G = None

        # init parameters

        # should smooth the original image using bilateral smoothing filter
        self.smooth_image = smooth_image

        # should use the thresholded gradient image for shortest path computation
        self.threshold_gradient_image = threshold_gradient_image

        # init image

        # store image and compute the gradient image
        self.image = image

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, value):
        self._image = value

        if self._image is not None:
            if self.smooth_image:
                self._smooth_image()

            self._compute_gradient_image()

            if self.threshold_gradient_image:
                self._threshold_gradient_image()

            self._compute_graph()

        else:
            self.edges = None
            self.G = None

    def _smooth_image(self):
        from skimage import restoration
        self._image = restoration.denoise_bilateral(self.image)

    def _compute_gradient_image(self):
        from skimage import filters
        self.edges = filters.scharr(self._image)

    def _threshold_gradient_image(self):
        from skimage.filters import threshold_otsu
        threshold = threshold_otsu(self.edges)
        self.edges = self.edges > threshold
        self.edges = self.edges.astype(float)

    def _compute_graph(self, norm_function=math.fabs):
        self.G = {}
        rows, cols = self.edges.shape
        for col in range(cols):
            for row in range(rows):

                neighbors = []
                if row > 0:
                    neighbors.append((row-1, col))

                if row < rows-1:
                    neighbors.append((row+1, col))

                if col > 0:
                    neighbors.append((row, col-1))

                if col < cols-1:
                    neighbors.append((row, col+1))

                dist = {}
                for n in neighbors:
                    # distance function can be replaced with a different norm
                    dist[n] = norm_function(self.edges[row][col] - self.edges[n[0], n[1]])

                self.G[(row, col)] = dist

    def compute_shortest_path(self, from_, to_, length_penalty=0.0):
        if self.image is None:
            raise AttributeError("Load an image first!")

        path = shortestPath(self.G, from_, to_, length_penalty=length_penalty)

        return path
