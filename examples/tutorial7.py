# -*- coding: utf-8 -*-
"""
This script shows how to embed the animation into a 
background image (it's also possible to embed the animation
into another animation, but that's too complicated to implement
in a simple program ...)
"""
from colorsys import hls_to_rgb
import gifmaze as gm
from gifmaze.algorithms import wilson, bfs
from gifmaze.utils import generate_text_mask


# firstly define the size and color_depth of the image.
width, height = 600, 400
color_depth = 8

# define a surface to draw on.
surface = gm.GIFSurface.from_image('teacher.png', color_depth)

# set the 0-th color to be the same with the blackboard's.
palette = [52, 51, 50, 200, 200, 200, 255, 0, 255]
for i in range(256):
    rgb = hls_to_rgb((i / 360.0) % 1, 0.5, 1.0)
    palette += [int(round(255 * x)) for x in rgb]

surface.set_palette(palette)

# next define an animation environment to run the algorithm.
anim = gm.Animation(surface)

# set the speed, delay, and transparent color we want.
anim.set_control(speed=50, delay=1, trans_index=3)

# add a maze instance.
mask = generate_text_mask(surface.size, 'UST', 'ubuntu.ttf', 350)
# specify the region that where the animation is embedded.
left, top, right, bottom = 66, 47, 540, 343
maze = anim.create_maze_in_region(cell_size=4,
                                  region=(left, top, right, bottom),
                                  mask=mask)

anim.pad_delay_frame(100)
# paint the blackboard
surface.rectangle(left, top, right - left + 1, bottom - top + 1, 0)

# in the first algorithm only 4 colors occur in the image, so we can use
# a smaller minimum code length, this will reduce the file size significantly.
surface.set_lzw_compress(2)

# pad one second delay, get ready!
anim.pad_delay_frame(100)

# the animation runs here.
wilson(maze, root=(0, 0))

# pad three seconds delay to see the result clearly.
anim.pad_delay_frame(300)

# now we run the maze solving algorithm.
# this time we use full 256 colors, hence the minimum code length is 8.
surface.set_lzw_compress(8)

# the tree and wall are unchanged throughout the maze solving algorithm hence
# it's safe to use 0 as the transparent color and color the wall and tree transparent.
anim.set_colormap({0: 0, 1: 0, 2: 2, 3: 3})
anim.set_control(speed=30, delay=5, trans_index=0)

# run the maze solving algorithm.
bfs(maze,
    start=(0, 0),
    end=(maze.size[0] - 1, maze.size[1] - 1))

# pad five seconds delay to see the path clearly.
anim.pad_delay_frame(500)

# save the result.
surface.save('wilson_bfs.gif')

surface.close()
