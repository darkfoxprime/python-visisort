"""
These classes implement the image renderers for visualizing a sorting method.

The instances of these classes are used with a ``RenderableArray``.
Each time the ``RenderableArray`` invokes the `render` method, the instances of
these classes re-generate an image (stored within the renderer) based on the
information provided to the `render` method.
"""

import time
import sys
import wx
import math
import functools


class Renderer(object):
    """The abstract base class for a Renderer."""

    def __init__(self, **kwargs):
        """
        Initialize the instance.

        The required keyword arguments are:
        * ``name``
          - the name of the renderer.

        The optional keyword arguments are:
        * ``description``
          - the description of the renderer.  (not currently used)
        """
        self.name = kwargs['name']
        self.description = kwargs.get('description', None)
        self.array = []
        self.read_count = 0
        self.write_count = 0
        self.read_index = None
        self.write_index = None
        self.is_sorted = True
        self.start_time = time.time()

    def render(
                self,
                read_index=None,
                write_index=None,
                array=None,
                read_count=None,
                write_count=None
            ):
        """
        Render the visualization after an array operation.

        All arguments to the method are optional:
        * ``read_index``
          - The index in the array that was just read.
            If not specified, it implies that _no_ read operation has
            taken place since the last call to `render`.
        * ``write_index``
          - The index in the array that was just written.
            If not specified, it implies that _no_ write operation has
            taken place since the last call to `render`.
        * ``read_count``
          - The number of times read operations have occurred.
            If not specified, the previous read count is left unchanged.
        * ``write_count``
          - The number of times write operations have occurred.
            If not specified, the previous write count is left unchanged.
        * ``array``
          - The array of values.
            If not specified, the previous array is left unchanged.
        """
        self.read_index = read_index
        self.write_index = write_index
        if read_count is not None:
            self.read_count = read_count
        if write_count is not None:
            self.write_count = write_count
        if array is not None:
            self.array = array
            self.is_sorted = functools.reduce(
                        lambda prev, idx: array[idx] == idx and prev,
                        range(len(array)),
                        True
                    )
        self.update()

    def done(self):
        """Render the final array after the sort is complete."""
        self.read_index = None
        self.write_index = None
        self.end_time = time.time()
        self.update(is_final=True)

    def update(self, is_final=False):
        """
        Update the rendered image.

        ``is_final`` will be ``True`` for the final update after the sort
        is complete.

        This must be implemented by a subclass.
        """
        raise NotImplementedError


class SummaryRenderer(Renderer):
    """
    A summarizing `Renderer`.

    This renderer simply reports the summary (read count, write count, and
    time taken) after the sort is completeself.
    """

    def __init__(self, **kwargs):
        """Initialize the instance."""
        super(SummaryRenderer, self).__init__(**kwargs)

    def update(self, is_final=False):
        """Report the summary information if this was the final update."""
        if is_final:
            print(
                        "{0}: " +
                        "read_count = {1}, " +
                        "write_count={2}, " +
                        "time = {3:.2g}s{4}".format(
                            self.name,
                            self.read_count,
                            self.write_count,
                            self.end_time - self.start_time,
                            "" if self.is_sorted else " ** NOT SORTED **"
                        )
                    )
            sys.stdout.flush()


class WriteRenderer(SummaryRenderer):
    """A variation of SummaryRenderer that shows the array after each write."""

    def update(self, is_final=False):
        """Display the array after each write operation."""
        if self.write_index:
            print("{0}: array = {1!r}".format(self.name, self.array))
        super(WriteRenderer, self).update(is_final)


class SynchronizedRenderer(Renderer):
    """A renderer that uses a `synchronizer` to sync read/write operations."""

    def __init__(self, **kwargs):
        """
        Initialisze the instance.

        This adds the following optional keyword to the object instantiation:
        * ``synchronizer``
          - If specified, this is the ``synchronizer`` class instance that
            will be used to synchronize each renderer.
        """
        super(SynchronizedRenderer, self).__init__(**kwargs)
        self.synchronizer = kwargs.get('synchronizer', None)
        if self.synchronizer:
            self.synchronizer.add(self)

    def update(self, is_final=False):
        """
        Synchronize the renderers.

        After the final update for this renderer, report to the synchronizer
        that this renderer is done.
        """
        if self.synchronizer:
            self.synchronizer.sync(self)
            if is_final:
                self.synchronizer.done(self)


class ImageRenderer(SynchronizedRenderer):
    """
    Render a SortableArray into an image.

    This is the abstract superclass for all the renderers which render the
    array into an image.
    """

    def __init__(self, **kwargs):
        """
        Initialize the instance.

        The optional ``size`` keyword argument gives the size of the image.
        If not specified, the size will default to ``480``.

        Note - the ``size`` might be used differently in the different
        ``ImageRenderer`` subclasses.
        """
        super(ImageRenderer, self).__init__(**kwargs)
        self.size = kwargs.get('size', 480)
        self.image = None

    def update(self, is_final=False):
        """
        Create and render the image which holds the visualized array.

        This creates the image itself, then calls other (overridable)
        methods to draw the background, draw the read or write index, if either
        exists, and draw the points of the array itself.
        """
        print("ImageRenderer[{0}] running update".format(self.name), flush=True)
        self.image = wx.Bitmap(self.size, self.size)
        mdc = wx.MemoryDC(self.image)
        self.draw_background(mdc, is_final)
        self.draw_indices(mdc, is_final)
        self.draw_points(mdc, is_final)
        mdc.SelectObject(wx.NullBitmap)
        super(ImageRenderer, self).update(is_final)

    def draw_background(self, mdc, is_final=False):
        """
        Draw the background of the image.

        This must be overridden by a subclass.
        """
        raise NotImplementedError

    def draw_indices(self, mdc, is_final=False):
        """
        Draw the read and/or write indices, if either or both exist.

        This must be overridden by a subclass.
        """
        raise NotImplementedError

    def draw_points(self, mdc, is_final=False):
        """
        Draw the points of the array.

        This must be overridden by a subclass.
        """
        raise NotImplementedError


class RectangleImageRenderer(ImageRenderer):
    """Render a SortableArray into a square (despite the name) image."""

    def draw_background(self, mdc, is_final=False):
        """
        Draw the background of the image.

        If the image is final, the background is cleared to black; if the image
        is not final, it's cleared to a very dark gray.  In either case, the
        name of the sorting method is printed centered at the top of the
        background (so that the name will not obscure the rendered array
        itself).
        """
        bg_rgb = 0 if is_final else 16
        bg_color = wx.Colour(bg_rgb, bg_rgb, bg_rgb)
        mdc.SetBackground(wx.Brush(bg_color))
        mdc.Clear()
        mdc.SetTextBackground(bg_color)
        mdc.SetTextForeground(wx.Colour(255, 255, 255))
        title = self.description if self.description is not None else self.name
        title_size = mdc.GetTextExtent(title)
        mdc.DrawText(title, (self.size - title_size.width) / 2, 2)

    def draw_indices(self, mdc, is_final=False):
        """
        Draw the read and/or write indices, if needed.

        The read index is drawn as a dark gray vertical line underneath the
        array location that was read.

        The write index is drawn as a light gray vertical line in the same
        location.

        This works by using the helper method, `coord_of_index_value()` to
        find the beginning of the line (at the read or write index with value
        `0`) and end of the line (at the read or write index with value equal
        to one less than the length of the array).  (This allows a subclass
        to change the geometry of the rendered image, by modifying
        `coord_of_index_value`, without affecting the functionality of the
        `draw_indices` and `draw_points` methods.)
        """
        if self.read_index is not None:
            mdc.SetPen(wx.Pen(wx.Colour(64, 64, 64)))
            mdc.DrawLine(
                        self.coord_of_index_value(self.read_index, 0),
                        self.coord_of_index_value(
                            self.read_index,
                            len(self.array) - 1
                        )
                    )
        if self.write_index is not None:
            mdc.SetPen(wx.Pen(wx.Colour(128, 128, 128)))
            mdc.DrawLine(
                        self.coord_of_index_value(self.write_index, 0),
                        self.coord_of_index_value(
                            self.write_index,
                            len(self.array) - 1
                        )
                    )

    def draw_points(self, mdc, is_final=False):
        """
        Draw the points of the array.

        Each point is drawn using a color that indicates how close or far away
        the point is from being correct, using the `color_of_index_value()`
        helper method.  The location of each point is obtained using the helper
        method `coord_of_index_value()`.

        (The use of the helper methods allows a subclass to change the geometry
        or the meaning of the colors of the rendered image, by modifying
        `color_of_index_value` and/or `coord_of_index_value`, without affecting
        the functionality of the `draw_indices` and `draw_points` methods.)
        """
        al = len(self.array)
        for i in range(al):
            mdc.SetPen(wx.Pen(self.color_of_index_value(i, self.array[i])))
            mdc.DrawPoint(self.coord_of_index_value(i, self.array[i]))

    def coord_of_index_value(self, idx, value):
        """Calculate the coordinates of a given array index and value."""
        x = idx * self.size / len(self.array)
        y = value * self.size / len(self.array)
        p = wx.Point(x, y)
        return p

    def color_of_index_value(self, idx, value):
        """Calculate the color for a given array index and value."""
        error = abs(value - idx)
        if value == idx:
            hue = 120.0
        else:
            if value < idx:
                max_error = idx
            elif value > idx:
                max_error = len(self.array) - 1 - idx
            hue = 60.0 * (max_error - error) / max_error
        # saturation = 1.0
        # value = 1.0
        # chroma = 255 * saturation * value
        # base = 255 * value * (1.0 - saturation)
        chroma = 255
        # base = 0
        hue_sextant = hue / 60.0
        component = chroma * (1 - abs(hue_sextant % 2 - 1))
        (r, g, b) = (
            (chroma, component, 0),
            (component, chroma, 0),
            (0, chroma, component),
            (0, component, chroma),
            (component, 0, chroma),
            (chroma, 0, component),
        )[int(hue_sextant)]
        # (r,g,b) = (r + base, g + base, b + base)
        c = wx.Colour(r, g, b)
        return c


class CircleImageRenderer(RectangleImageRenderer):
    """
    This renders the array in a circular geometry.

    The geometry is chosen such that a sorted array renders as a spiral.

    This subclasses off of `RectangleImageRenderer` and just changes the
    definition of `coord_of_index_value()`, treating the array index and
    value as polar coordinates instead of cartesian coordinates.
    """

    def coord_of_index_value(self, idx, value):
        """Calculate the coordinates of a given array index and value."""
        a = -idx * math.pi * 2 / len(self.array)
        half = self.size / 2
        r = value * half / len(self.array)
        x = int(r * math.cos(a) + half)
        y = int(r * math.sin(a) + half)
        #print("generating point {0!r}".format((x, y)), end='', file=sys.stdout, flush=True)
        p = wx.Point(x, y)
        #print("...generated {0!r}".format(p), file=sys.stdout, flush=True)
        return p
