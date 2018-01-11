# -*- coding: utf-8 -*-

from io import BytesIO
from PIL import Image
from .encoder import (Compression,
                      screen_descriptor,
                      image_descriptor,
                      loop_control_block,
                      global_color_table)


class GIFSurface(object):
    """
    A GIFSurface is an object on which the animations are drawn,
    and which can be saved as GIF images.
    
    Each instance opens a BytesIO file in memory onces it's created.
    The frames are temporarily written to this in-memoty file for speed.
    
    When the animation is finished one should call the `close()` method
    to close the io.
    """
    def __init__(self, width, height, color_depth, palette=None,
                 loop=0, bg_color=None, min_code_length=None):
        """
        Parameters
        
        width, height: size of the image in pixels.
        
        color_depth: color depth of the image (minimum bits needed to
            represent the colors in the image).
        
        palette: the global color table.
        
        loop: number of loops of the image.
        
        bg_color: background color index.
        
        min_code_length: minimum code length of the LZW encoder.
        """
        self.size = (width, height)
        self.loop = loop
        self._io = BytesIO()
        
        if not isinstance(color_depth, int) and 1 <= color_depth <= 8:
            raise ValueError('Invalid color depth.')
        self.color_depth = color_depth
        
        if not palette:
            palette = [0] * (3 * 1 << self.color_depth)
        self.set_palette(palette)

        if not min_code_length:
            min_code_length = self.color_depth
        self.set_lzw_compress(min_code_length)

        if bg_color is not None:
            self.rectangle(0, 0, width, height, bg_color)
            
    def __str__(self):
        return '{0}({1}x{2}, color depth: {3}, loop: {4})'.format(self.__class__.__name__,
                                                                  self.size[0], self.size[1],
                                                                  self.color_depth,
                                                                  self.loop)
      
    __repr__ = __str__
    
    def set_palette(self, palette):
        """Set the palette of the surface."""
        self.palette = global_color_table(self.color_depth, palette)
        
    def set_lzw_compress(self, min_code_length):
        n = max(2, min(12, min_code_length))
        self._lzw_compress = Compression(n)
        
    def write(self, data):
        self._io.write(data)
        
    def compress(self, data):
        return self._lzw_compress(data)
      
    def rectangle(self, left, top, width, height, color):
        """
        Draw a rectangle with left-top corner at `(left, top)`
        and size `(width, height)`. `color` is the index of the
        color in the global color table.
        """
        descriptor = image_descriptor(left, top, width, height)
        data = Compression(2)([color] * width * height)
        self.write(descriptor + data)

    @property
    def _gif_header(self):
        """
        Get the `logical screen descriptor`, `global color table`
        and `loop control block`.
        """
        screen = screen_descriptor(self.size[0], self.size[1], self.color_depth)
        loop = loop_control_block(self.loop)
        return screen + self.palette + loop

    def save(self, filename):
        """
        Save the animation to a .gif file, note the 'wb' mode here!
        """     
        with open(filename, 'wb') as f:
            f.write(self._gif_header)
            f.write(self._io.getvalue())
            f.write(bytearray([0x3B]))

    def clear(self):
        """
        Clear the contents in the io by creating a new one.
        """
        self._io.close()
        self._io = BytesIO()
        
    def close(self):
        self._io.close()

    @classmethod
    def from_image(cls, img_file, *args, **kwargs):
        """
        Create a surface from a given image file.
        The size of the returned surface is the same with the image's.
        The image is then painted as the background.
        
        -------
        Example:
        
        >>> surface = GIFSurface.from_image('teacher.png', color_depth=8)
        >>> surface.save('test_surface.gif')
        >>> surface.close()
        """
        # the image file usually contains more than 256 colors
        # so we need to convert it to gif format first.
        with BytesIO() as temp_io:
            Image.open(img_file).convert('RGB').save(temp_io, format='gif')
            img = Image.open(temp_io).convert('RGB')
            kwargs['bg_color'] = None
            surface = cls(img.size[0], img.size[1], *args, **kwargs)

            # iterate over all pixels to get the global color table and indices list.
            data = list(img.getdata())
            colors = []
            indices = []
            count = 0
        
            for c in data:
                if c not in colors:
                    colors.append(c)
                    indices.append(count)
                    count += 1
                else:
                    i = colors.index(c)
                    indices.append(i)
          
            palette = []
            for c in colors:
                palette += c
           
            # here we do not bother about how many colors are actually in the image,
            # we simply use full 256 colors.
            if len(palette) < 3 * 256:
                palette += [0] * (3 * 256 - len(palette))
            
            descriptor = image_descriptor(0, 0, img.size[0], img.size[1], 0b10000111)
            compressed_data = Compression(8)(indices)
            surface.write(descriptor + bytearray(palette) + compressed_data)

        return surface
