
import time
import sys
import wx
import math

class Renderer(object):
    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.description = kwargs.get('description', None)
        self.array = []
        self.read_count = 0
        self.write_count = 0
        self.read_index = None
        self.write_index = None
        self.is_sorted = True
        self.start_time = time.time()

    def render(self, read_index=None, write_index=None, array=None, read_count=None, write_count=None):
        self.read_index = read_index
        self.write_index = write_index
        if read_count is not None:  self.read_count  = read_count
        if write_count is not None: self.write_count = write_count
        if array is not None:
            self.array     = array
            self.is_sorted = reduce(lambda prev,idx:array[idx] == idx and prev, xrange(len(array)), True)
        self.update()

    def done(self):
        self.read_index = None
        self.write_index = None
        self.end_time = time.time()
        self.update(is_final = True)

    def update(self, is_final = False):
        raise NotImplementedError

class SummaryRenderer(Renderer):

    def __init__(self, **kwargs):
        super(SummaryRenderer,self).__init__(**kwargs)

    def update(self, is_final = False):
        if is_final:
            print "{0}: read_count = {1}, write_count = {2}, time = {3:.2g}s{4}".format(self.name, self.read_count, self.write_count, self.end_time - self.start_time, "" if self.is_sorted else " ** NOT SORTED **")
            sys.stdout.flush()

class WriteRenderer(SummaryRenderer):
    def update(self, is_final = False):
        if self.write_index:
            print "{0}: array = {1!r}".format(self.name, self.array)
        super(WriteRenderer,self).update(is_final)

class SynchronizedRenderer(Renderer):
    def __init__(self, **kwargs):
        super(SynchronizedRenderer,self).__init__(**kwargs)
        self.synchronizer = kwargs.get('synchronizer', None)
        if self.synchronizer: self.synchronizer.add(self)

    def update(self, is_final = False):
        if self.synchronizer:
            self.synchronizer.sync(self)
            if is_final:
                self.synchronizer.done(self)


class RectangleImageRenderer(SynchronizedRenderer):
    def __init__(self, **kwargs):
        super(RectangleImageRenderer,self).__init__(**kwargs)
        self.size = kwargs.get('size', 480)

    def update(self, is_final = False):
        self.image = wx.Bitmap(self.size, self.size)
        mdc = wx.MemoryDC(self.image)
        self.draw_background(mdc, is_final)
        self.draw_indices(mdc, is_final)
        self.draw_points(mdc, is_final)
        mdc.SelectObject(wx.NullBitmap)
        super(RectangleImageRenderer,self).update(is_final)

    def draw_background(self, mdc, is_final = False):
        bg_rgb = 0 if is_final else 16
        bg_color = wx.Colour(bg_rgb, bg_rgb, bg_rgb)
        mdc.SetBackground(wx.Brush(bg_color))
        mdc.Clear()
        mdc.SetTextBackground(bg_color)
        mdc.SetTextForeground(wx.Colour(255,255,255))
        title = self.description if self.description is not None else self.name
        title_size = mdc.GetTextExtent(title)
        mdc.DrawText(title, (self.size - title_size.width)/2, 2)

    def draw_indices(self, mdc, is_final = False):
        if self.read_index is not None:
            mdc.SetPen(wx.Pen(wx.Colour(64,64,64)))
            mdc.DrawLine(self.coord_of_index_value(self.read_index,0), self.coord_of_index_value(self.read_index, len(self.array)-1))
        if self.write_index is not None:
            mdc.SetPen(wx.Pen(wx.Colour(128,128,128)))
            mdc.DrawLine(self.coord_of_index_value(self.write_index,0), self.coord_of_index_value(self.write_index, len(self.array)-1))

    def draw_points(self, mdc, is_final = False):
        al = len(self.array)
        for i in range(al):
            mdc.SetPen(wx.Pen(self.color_of_index_value(i, self.array[i])))
            mdc.DrawPoint(self.coord_of_index_value(i, self.array[i]))

    def coord_of_index_value(self, idx, value):
        x = idx * self.size / len(self.array)
        y = value * self.size / len(self.array)
        return wx.Point(x,y)

    def color_of_index_value(self, idx, value):
        r = abs(value - idx) * 256 / len(self.array)
        g = 255 - r
        b = 0
        return wx.Colour(r, g, b)

class CircleImageRenderer(RectangleImageRenderer):
    def __init__(self, **kwargs):
        super(CircleImageRenderer,self).__init__(**kwargs)

    def coord_of_index_value(self, idx, value):
        a = -idx * math.pi*2 / len(self.array)
        half = self.size / 2
        r = value * half / len(self.array)
        x = int(r*math.cos(a) + half)
        y = int(r*math.sin(a) + half)
        return wx.Point(x,y)
