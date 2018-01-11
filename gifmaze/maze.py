# -*- coding: utf-8 -*-

from PIL import Image


class Maze(object):
    """
    This class defines the basic structure of a maze and some operations on it.
    A maze is represented by a grid with `height` rows and `width` columns,
    each cell in the maze has 4 possible states:
    0: it's a wall
    1: it's in the tree
    2: it's in the path
    3: it's filled (this will not be used until the maze-searching animation)
    Initially all cells are walls.
    Adjacent cells in the maze are spaced out by one cell.
    """

    WALL = 0
    TREE = 1
    PATH = 2
    FILL = 3

    def __init__(self, width, height, mask):
        """
        Parameters
        ----------
        width, height: size of the maze, must both be odd integers.
        
        mask: `None` or an file-like image or an instance of PIL's Image class.
              If not `None` then this mask image must be of binary type:
              the black pixels are considered as `walls` and are overlayed
              on top of the grid graph. Note the walls must preserve the
              connectivity of the grid graph, otherwise the program will
              not terminate.
        """
        if (width * height % 2 == 0):
            raise ValueError('The width and height must both be odd integers.')
        
        self.size = (width, height)
        self._grid = [[0] * height for _ in range(width)]
        self._num_changes = 0   # a counter holds how many cells are changed.
        self._frame_box = None  # a 4-tuple maintains the region that to be updated.

        if mask is not None:
            if isinstance(mask, Image.Image):
                mask = mask.convert('L').resize(self.size)
            else:
                mask = Image.open(mask).convert('L').resize(self.size)

        def get_mask_pixel(cell):
            return mask is None or mask.getpixel(cell) == 255

        self.cells = []
        for y in range(0, height, 2):
            for x in range(0, width, 2):
                if get_mask_pixel((x, y)):
                    self.cells.append((x, y))

        def neighborhood(cell):
            x, y = cell
            neighbors = []
            if x >= 2 and get_mask_pixel((x - 2, y)):
                neighbors.append((x - 2, y))
            if y >= 2 and get_mask_pixel((x, y - 2)):
                neighbors.append((x, y - 2))
            if x <= width - 3 and get_mask_pixel((x + 2, y)):
                neighbors.append((x + 2, y))
            if y <= height - 3 and get_mask_pixel((x, y + 2)):
                neighbors.append((x, y + 2))
            return neighbors

        self._graph = {v: neighborhood(v) for v in self.cells}

    def __str__(self):
        return '{0}({1}x{2})'.format(self.__class__.__name__, self.width, self.height)

    __repr__ = __str__

    def get_neighbors(self, cell):
        return self._graph[cell]

    def mark_cell(self, cell, value):
        """Mark a cell and update `frame_box` and `num_changes`."""
        x, y = cell
        self._grid[x][y] = value
        self._num_changes += 1
        
        if self._frame_box is not None:
            left, top, right, bottom = self._frame_box
            self._frame_box = (min(x, left),  min(y, top),
                               max(x, right), max(y, bottom))
        else:
            self._frame_box = (x, y, x, y)

    def mark_space(self, c1, c2, value):
        """Mark the space between two adjacent cells."""
        c = ((c1[0] + c2[0]) // 2, (c1[1] + c2[1]) // 2)
        self.mark_cell(c, value)
        
    def mark_path(self, path, value):
        """Mark the cells in a path and the spaces between them."""
        for cell in path:
            self.mark_cell(cell, value)
        for c1, c2 in zip(path[1:], path[:-1]):
            self.mark_space(c1, c2, value)

    def get_cell(self, cell):
        x, y = cell
        return self._grid[x][y]

    def barrier(self, c1, c2):
        """Check if two adjacent cells are connected."""
        x = (c1[0] + c2[0]) // 2
        y = (c1[1] + c2[1]) // 2
        return self._grid[x][y] == Maze.WALL
    
    def is_wall(self, cell):
        x, y = cell
        return self._grid[x][y] == Maze.WALL
    
    def in_tree(self, cell):
        x, y = cell
        return self._grid[x][y] == Maze.TREE

    def in_path(self, cell):
        x, y = cell
        return self._grid[x][y] == Maze.PATH

    def reset(self):
        self._num_changes = 0
        self._frame_box = None
                    
    @property
    def frame_box(self):
        return self._frame_box
    
    @property
    def num_changes(self):
        return self._num_changes
    
    def bind_animation(self, anim):
        """
        Bind this maze to an animation.
        This is for communicating with an Animation object.
        """
        self.anim = anim
