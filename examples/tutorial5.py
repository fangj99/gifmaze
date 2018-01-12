# -*- coding: utf-8 -*-
"""
This script shows how to use a mask image in a maze.
"""
import gifmaze as gm
from gifmaze.algorithms import random_dfs
from gifmaze.utils import generate_text_mask


# firstly define the size and color_depth of the image.
width, height = 600, 400
color_depth = 2

# define a surface to draw on.
surface = gm.GIFSurface(width, height, color_depth, bg_color=0)

# define the colors of the wall, tree and transparent channel.
surface.set_palette([0, 0, 0, 200, 200, 200, 255, 0, 255, 0, 0, 0])

# next define an animation environment to run the algorithm.
anim = gm.Animation(surface)

# set the speed, delay, and transparent color we want.
anim.set_control(speed=20, delay=5, trans_index=3)

# now we need to add a maze instance.
# we generate a mask image first: (you may also use a image file, provided
# that it preserves the connectivity of the grid)
mask = generate_text_mask(surface.size, 'UST', 'ubuntu.ttf', 300)

# `region=5` means the maze is padded with border of 5 pixels.
maze = anim.create_maze_in_region(cell_size=5, region=5, mask=mask)

# pad two seconds delay, get ready!
anim.pad_delay_frame(200)

# the animation runs here.
random_dfs(maze, start=(0, 0))

# pad five seconds delay to see the result clearly.
anim.pad_delay_frame(500)

# save the result.
surface.save('random_dfs.gif')

surface.close()
