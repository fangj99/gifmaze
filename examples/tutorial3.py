# -*- coding: utf-8 -*-
"""
This script shows the basic usage of the Surface class.
"""
import gifmaze as gm


width, height = 600, 400
color_depth = 1

surface = gm.GIFSurface(width, height, color_depth, bg_color=0)
surface.save('surface.gif')
surface.close()


surface = gm.GIFSurface.from_image('teacher.png', color_depth)
surface.save('teacher.gif')
surface.close()
