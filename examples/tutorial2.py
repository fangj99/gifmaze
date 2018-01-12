# -*- coding: utf-8 -*-
"""
This script generates a GIF image that contains three frames.
The delay of each frame is 1 second.
"""
import gifmaze.encoder as encoder

# size of the image.
width, height = 300, 300

# the palette contains 4 colors.
color_depth = 2

# always begins with the logical screen descriptor.
screen = encoder.screen_descriptor(width, height, color_depth)

# then follows the global color table.
palette = bytearray([255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0])

# the loop control block.
loop_control = encoder.loop_control_block(0)

# the graphics control block (delay, transpaernt)
graphics_control = encoder.graphics_control_block(100, None)

# the image descriptor.
descriptor = encoder.image_descriptor(0, 0, width, height)

# now add the data of each frame.
compress = encoder.Compression(color_depth)
data = bytearray()
for i in range(3):
    data += graphics_control + descriptor + compress([i] * width * height)

trailor = bytearray([0x3B])

with open('tutorial2.gif', 'wb') as f:
    f.write(screen
            + palette
            + loop_control
            + data
            + trailor)
