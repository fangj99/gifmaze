# -*- coding: utf-8 -*-
"""
This script generates a single static gif image of red color.
The loop control block and graphics control block are not needed.
"""
import gifmaze.encoder as encoder

# size of the image.
width, height = 100, 100

# 1 is the minimum color depth, it means that there are two
# colors in the global color table.
color_depth = 1

# all gif files begin with the logical screen descriptor.
screen = encoder.screen_descriptor(width, height, color_depth)

# then follows the global color table,
# here it contains two colors: red and black.
palette = bytearray([255, 0, 0, 0, 0, 0])

# the next is the image descriptor of the frame.
descriptor = encoder.image_descriptor(0, 0, width, height)

# then the LZW compressed pixel data.
# note the minimum code length is at least 2.
data = encoder.Compression(2)([0] * width * height)

# the file ends with the trailor '0x3B'.
trailor = bytearray([0x3B])

# finally put them together.
with open('tutorial1.gif', 'wb') as f:
    f.write(screen
            + palette
            + descriptor
            + data
            + trailor)
