# -*- coding: utf-8 -*-
"""
~~~~~~~~~~~~~~~~~~~~
A simple GIF encoder
~~~~~~~~~~~~~~~~~~~~

Structure of a GIF file: (in the order they appear)
    1. always begins with the logical screen descriptor.
    2. then follows the global color table.
    3. then follows the loop control block (specify the number of loops).
    4. then follows the image data of the frames,
       each frame is further divided into:
       (i) a graphics control block that specify the delay and
           transparent color of this frame.
       (ii) the image descriptor.
       (iii) the LZW encoded data.
    5. finally the trailor '0x3B'.

Reference for the GIF89a specification:

    http://giflib.sourceforge.net/whatsinagif/index.html
"""
from struct import pack


class DataBlock(object):
    """
    Write bits into a bytearray and then pack this bytearray into data blocks.
    This class is used in the Lempel-Ziv-Welch compression algorithm when
    encoding maze into frames.
    """

    def __init__(self):
        self._bitstream = bytearray()  # write bits into this array
        self._nbits = 0  # a counter holds how many bits have been written

    def encode_bits(self, num, size):
        """
        Given a number `num`, encode it as a binary string of length `size`,
        and pack it at the end of bitstream.
        Example: num = 3, size = 5. The binary string for 3 is '00011' (it's
        '0b00011' in python), here we padded extra zeros at the left to make
        its length to be 5. The tricky part is that in a gif file, the encoded
        binary data stream increases from lower (least significant) bits to higher
        (most significant) bits, so we have to reverse it as '11000' and pack
        this string at the end of bitstream!
        """
        string = bin(num)[2:].zfill(size)
        for digit in reversed(string):
            if len(self._bitstream) * 8 == self._nbits:
                self._bitstream.append(0)
            if digit == '1':
                self._bitstream[-1] |= 1 << self._nbits % 8
            self._nbits += 1

    def dump_bytes(self):
        """
        Pack the LZW encoded image data into blocks.
        Each block is of length <= 255 and is preceded by a byte
        in 0-255 that indicates the length of this block.
        Each time after this function is called `_nbits` and
        `_bitstream` are reset to 0 and empty.
        """
        bytestream = bytearray()
        while len(self._bitstream) > 255:
            bytestream.append(255)
            bytestream.extend(self._bitstream[:255])
            self._bitstream = self._bitstream[255:]
        if len(self._bitstream) > 0:
            bytestream.append(len(self._bitstream))
            bytestream.extend(self._bitstream)

        self._nbits = 0
        self._bitstream = bytearray()
        return bytestream


class Compression(object):
    """
    The Lempel-Ziv-Welch compression algorithm used by the GIF89a specification.
    """

    def __init__(self, min_code_length):
        """
        min_code_length: an integer between 2 and 12.

        GIF allows the minimum code length as small as 2 and as large as 12.
        Even there are only two colors, the minimum code length must be at least 2.

        Note this is not actually the smallest code length that is used
        in the encoding process since the minimum code length tells us
        how many bits are needed just for the different colors of the image,
        we still have to account for the two special codes `end` and `clear`.
        Therefore the actual smallest code length that will be used is one more
        than `min_code_length`.
        """
        if not isinstance(min_code_length, int) \
        and not 2 <= min_code_length <= 12:
            raise ValueError('Invalid minimum code length.')

        self._stream = DataBlock()
        self._min_code_length = min_code_length
        self._clear_code = 1 << min_code_length
        self._end_code = self._clear_code + 1
        self._max_codes = 4096

    def __call__(self, input_data):
        """
        input_data: a 1-d list consists of integers in range [0, 255],
            these integers are the indices of the colors of the pixels
            in the global color table.

        We do not check the validity of the input data here for efficiency.
        """
        # this is actually the minimum code length used
        code_length = self._min_code_length + 1
        next_code = self._end_code + 1
        # the default initial dict
        code_table = {(i,): i for i in range(1 << self._min_code_length)}
        # output the clear code
        self._stream.encode_bits(self._clear_code, code_length)

        pattern = tuple()
        for c in input_data:
            pattern += (c,)
            if pattern not in code_table:
                # add new code to the table
                code_table[pattern] = next_code
                # output the prefix
                self._stream.encode_bits(code_table[pattern[:-1]], code_length)
                pattern = (c,)  # suffix becomes the current pattern

                next_code += 1
                if next_code == 2**code_length + 1:
                    code_length += 1
                if next_code == self._max_codes:
                    next_code = self._end_code + 1
                    self._stream.encode_bits(self._clear_code, code_length)
                    code_length = self._min_code_length + 1
                    code_table = {(i,): i for i in range(1 << self._min_code_length)}

        self._stream.encode_bits(code_table[pattern], code_length)
        self._stream.encode_bits(self._end_code, code_length)
        return bytearray([self._min_code_length]) + self._stream.dump_bytes() + bytearray([0])


def screen_descriptor(width, height, color_depth):
    """
    This block specifies both the size of the image and its global color table.
    """
    byte = 0b10000000 | (color_depth - 1) | (color_depth - 1) << 4
    return pack('<6s2H3B', b'GIF89a', width, height, byte, 0, 0)


def loop_control_block(loop):
    """
    This block specifies the number of loops (0 means loop infinitely).
    """
    return pack('<3B8s3s2BHB', 0x21, 0xFF, 11, b'NETSCAPE', b'2.0', 3, 1, loop, 0)


def graphics_control_block(delay, trans_index=None):
    """
    This block specifies the delay and transparent color of the coming frame.
    `trans_index=None` means no transparent color.
    For static frames this block is not added.
    """
    if trans_index is None:
        return pack("<4BH2B", 0x21, 0xF9, 4, 0b00000100, delay, 0, 0)
    else:
        return pack("<4BH2B", 0x21, 0xF9, 4, 0b00000101, delay, trans_index, 0)


def image_descriptor(left, top, width, height, byte=0):
    """
    This block specifies the position of the coming frame (relative to the window)
    and whether it has a local color table or not.
    """
    return pack('<B4HB', 0x2C, left, top, width, height, byte)

def global_color_table(color_depth, palette):
    """
    Return a valid global color table.
    The global color table of a GIF image is a 1-d bytearray of the form
    [r1, g1, b1, r2, g2, b2, ...] with length equals to 2**n where n is
    the color depth of the image.

    ----------
    Parameters

    color_depth: color depth of the GIF.

    palette: a list of rgb colors of the format [r1, g1, b1, r2, g2, b2, ...].
        The number of colors must be greater than or equal to 2**n where n is
        the color depth. Redundant colors will be discarded.
    """
    try:
        palette = bytearray(palette)
    except:
        raise ValueError('Cannot convert palette to bytearray.')

    valid_length = 3 * (1 << color_depth)
    if len(palette) < valid_length:
        raise ValueError('Invalid palette length.')
    if len(palette) > valid_length:
        palette = palette[:valid_length]

    return palette
