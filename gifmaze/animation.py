# -*- coding: utf-8 -*-

from .maze import Maze
from .surface import GIFSurface
from .encoder import (graphics_control_block, image_descriptor)


class Animation(object):
    """
    This class builds the environment for encoding an animation into a GIF file.
    It controls how a maze is colored and rendered to the GIF Surface.
    """

    def __init__(self, surface):
        """
        `surface` is an instance of the Surface class.
        """
        if not isinstance(surface, GIFSurface):
            raise TypeError('An instance of GIFSurface is expected.')

        self._surface = surface
        self.num_colors = 1 << surface.color_depth
        self.colormap = {i: i for i in range(self.num_colors)}
                                 # a dict that maps the value of a cell to its color index.
        self.speed = 10          # output the frame once this number of cells are changed.
        self.trans_index = None  # the index of the transparent color in the global color table.
        self.delay = 5           # delay between successive frames.
        self.cell_size = 5       # size of a cell in the image.
        self.translation = (0, 0)
                                 # location of the top-left corner of the animation.

    def set_colormap(self, cmap):
        """
        Control how the cells are mapped to the colors.

        cmap: a dict that maps the value of a cell to a color index.
        Example:

        >>> cmap = {0: 1, 1: 2, 2: 3}
        >>> self.set_colormap(cmap)

        Here a pair {k: i} means the cells with value=k are
        mapped to the color of index i (in the global color table).
        """
        if isinstance(cmap, dict):
            self.colormap.update(cmap)

    def set_control(self, **kwargs):
        """
        Control the speed, delay and transparent channel of the animation.
        """
        params = ['speed', 'delay', 'trans_index']
        for key, val in kwargs.items():
            if key in params:
                setattr(self, key, val)

    def pad_delay_frame(self, delay):
        """
        Pad a 1x1 transparent frame for delay (it's invisible).
        """
        control = graphics_control_block(delay, self.trans_index)
        descriptor = image_descriptor(0, 0, 1, 1)
        self._surface.write(control + descriptor + self._surface.compress([self.trans_index]))

    def refresh_frame(self):
        """Update a frame in the animation and write it into the file."""
        if self.maze.num_changes >= self.speed:
            self._surface.write(self._encode_frame())

    def clear_remaining_changes(self):
        """Clear possibly remaining changes when the animation is finished."""
        if self.maze.num_changes > 0:
            self._surface.write(self._encode_frame())

    def _encode_frame(self):
        """Encode current maze into one frame and return the encoded data."""
        # 1. the graphics control block
        control = graphics_control_block(self.delay, self.trans_index)
        # 2. the image descriptor of this frame
        if self.maze.frame_box is not None:
            left, top, right, bottom = self.maze.frame_box
        else:
            left, top, right, bottom = 0, 0, self.maze.size[0] - 1, self.maze.size[1] - 1

        width = right - left + 1
        height = bottom - top + 1
        descriptor = image_descriptor(self.cell_size * left + self.translation[0],
                                      self.cell_size * top  + self.translation[1],
                                      self.cell_size * width,
                                      self.cell_size * height)

        # A generator that yields the pixels of this frame. This may look a bit unintuitive
        # because encoding frames will be called thousands of times in an animation and
        # we should avoid creating and destroying a new list each time it's called.
        def get_frame_pixels():
            for i in range(width * height * self.cell_size * self.cell_size):
                y = i // (width * self.cell_size * self.cell_size)
                x = (i % (width * self.cell_size)) // self.cell_size
                val = self.maze.get_cell((x + left, y + top))
                yield self.colormap[val]

        # 3. the compressed image data of this frame
        data = self._surface.compress(get_frame_pixels())

        # clear `num_changes` and `frame_box`
        self.maze.reset()

        return control + descriptor + data

    def add_maze(self, maze, cell_size, translation):
        self.maze = maze
        self.cell_size = cell_size
        self.translation = translation
        self.maze.bind_animation(self)
        return self.maze

    def create_maze_in_region(self, cell_size, region, mask):
        """
        Create a maze in a given region. The returned maze may be
        adjusted to make it located at the center of the region.

        ----------
        Parameters

        cell_size: size of a cell of the maze in pixels.

        region: an int or a 4-tuple (x1, y1, x2, y2) that specify
            the top-left and bottom-right corners of the region.

        mask: the mask image.
        """
        if isinstance(region, int):
            left, top, right, bottom = (region,
                                        region,
                                        self._surface.size[0] - region - 1,
                                        self._surface.size[1] - region - 1)
        else:
            left, top, right, bottom = region

        w, r = divmod(right - left + 1, cell_size)
        if w % 2 == 0:
            w -= 1
            left += (cell_size + r) // 2

        h, r = divmod(bottom - top + 1, cell_size)
        if h % 2 == 0:
            h -= 1
            top += (cell_size + r) // 2

        maze = Maze(w, h, mask)
        return self.add_maze(maze, cell_size, (left, top))
