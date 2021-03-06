import utils

utils.mem('matrix_frame1')
from adafruit_display_text import bitmap_label
utils.mem('matrix_frame2')
import bitmaptools
utils.mem('matrix_frame3')
import board
utils.mem('matrix_frame4')
import cctime
utils.mem('matrix_frame5')
import displayio
utils.mem('matrix_frame6')
import frame
utils.mem('matrix_frame7')
import framebufferio
utils.mem('matrix_frame8')
import rgbmatrix
utils.mem('matrix_frame9')
from ulab import numpy as np
utils.mem('matrix_frame10')

# TODO: BIT_DEPTH should normally be set to 5.  It is set to 2 in order to
# conserve memory and avoid MemoryErrors.  Once memory issues are fixed,
# this should be changged back to 5 to get good colour rendering and better
# brightness control.
BIT_DEPTH = 2
MIN_RGB_VALUE = 0x100 >> BIT_DEPTH


def new_display_frame(w, h, depth, fontlib):
    displayio.release_displays()
    return MatrixFrame(w, h, depth, fontlib, rgbmatrix.RGBMatrix(
        width=192, height=32, bit_depth=BIT_DEPTH,
        rgb_pins=[
            board.MTX_R1, board.MTX_G1, board.MTX_B1,
            board.MTX_R2, board.MTX_G2, board.MTX_B2
        ],
        addr_pins=[
            board.MTX_ADDRA, board.MTX_ADDRB, board.MTX_ADDRC, board.MTX_ADDRD
        ],
        clock_pin=board.MTX_CLK,
        latch_pin=board.MTX_LAT,
        output_enable_pin=board.MTX_OE
    ))


def apply_brightness(brightness, r, g, b):
    # When scaling down, don't scale down any nonzero values to zero.
    min_r = MIN_RGB_VALUE if r else 0
    min_g = MIN_RGB_VALUE if g else 0
    min_b = MIN_RGB_VALUE if b else 0
    return (
        max(min_r, int(brightness * r)),
        max(min_g, int(brightness * g)),
        max(min_b, int(brightness * b))
    )


class MatrixFrame(frame.Frame):
    def __init__(self, w, h, depth, fontlib=None, matrix=None):
        """Creates a Frame with a given width and height.  Coordinates of the
        top-left and bottom-right pixels are (0, 0) and (w - 1, h - 1)."""
        self.w = w
        self.h = h
        self.depth = depth
        self.bitmap = displayio.Bitmap(w, h, depth)
        self.display = None
        self.fontlib = fontlib
        if matrix:
            self.display = framebufferio.FramebufferDisplay(
                matrix, auto_refresh=False)

            self.shader = displayio.Palette(depth)
            self.colours = [(0, 0, 0)] * self.depth
            self.brightness = 1.0
            self.next_cv = 1

            self.layer = displayio.TileGrid(self.bitmap, pixel_shader=self.shader)
            self.group = displayio.Group()
            self.group.append(self.layer)
            self.display.show(self.group)
            self.error_label = None

    def set_brightness(self, brightness):
        self.brightness = brightness
        for cv in range(self.next_cv):
            sr, sg, sb = apply_brightness(self.brightness, *self.colours[cv])
            self.shader[cv] = ((sr << 16) | (sg << 8) | sb)

    def pack(self, r, g, b):
        if self.next_cv < self.depth:
            self.colours[self.next_cv] = (r, g, b)
            sr, sg, sb = apply_brightness(self.brightness, r, g, b)
            self.shader[self.next_cv] = ((sr << 16) | (sg << 8) | sb)
            self.next_cv += 1
        return self.next_cv - 1

    def send(self):
        self.display.refresh(minimum_frames_per_second=0)
        # Display bug: refresh() doesn't cause a refresh unless we also set
        # auto_refresh = False (even though auto_refresh is already False!).
        self.display.auto_refresh = False

    def get(self, x, y):
        return self.bitmap[x, y]

    def set(self, x, y, cv):
        self.bitmap[x, y] = cv

    def fill(self, x, y, w, h, cv):
        x, y, w, h = frame.clamp_rect(x, y, w, h, self.w, self.h)
        bitmaptools.fill_region(self.bitmap, x, y, x + w, y + h, cv)

    def paste(self, x, y, source, sx=None, sy=None, w=None, h=None, cv=None):
        if source.w == 0 or source.h == 0:
            return
        x, y, sx, sy, w, h = frame.intersect(self, x, y, source, sx, sy, w, h)
        self.bitmap.blit(
            x, y, source.bitmap, x1=sx, y1=sy, x2=sx+w, y2=sy+h, write_value=cv)

    def new_label(self, text, font_id):
        font = self.fontlib.get(font_id)
        if not self.error_label:
            self.error_label = LabelFrame('[MemoryError] ', font)
        try:
            return LabelFrame(text, font)
        except MemoryError as e:
            utils.report_error(e, f'Failed to draw "{text}"')
            return self.error_label


class LabelFrame(frame.Frame):
    def __init__(self, text, font):
        label = bitmap_label.Label(font, text=text, save_text=False)
        self.bitmap = label.bitmap
        # label.bitmap can be None if there is no text to render
        self.w = label.bitmap.width if label.bitmap else 0
        self.h = label.bitmap.height if label.bitmap else 0
