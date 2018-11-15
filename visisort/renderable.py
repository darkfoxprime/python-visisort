"""
This is the base class for the sort visualizer.

This class takes care of all the array-type stuff, and counts how many
array accesses are made.
"""

from visisort.sortable import SortableArray


class RenderableArray(SortableArray):
    """
    A SortableArray that invokes an image renderer for array accesses.

    See the ``renderer`` class for information about the renderers.
    """

    def __init__(self, iterable=(), renderer=None):
        """Initialize the RenderableArray."""
        super(RenderableArray, self).__init__(iterable)
        self.renderer = renderer
        self.renderer.render(array=self.ary)

    def __getitem__(self, key):
        """Implement ``[]`` getter."""
        value = self.ary.__getitem__(key)
        self.readcount += 1
        if self.renderer:
            self.renderer.render(
                        read_index=key,
                        array=self.ary,
                        read_count=self.readcount
                    )
        return value

    def __setitem__(self, key, value):
        """Implement ``[]`` setter."""
        self.ary.__setitem__(key, value)
        self.writecount += 1
        if self.renderer:
            self.renderer.render(
                        write_index=key,
                        array=self.ary,
                        write_count=self.writecount
                    )

    def __delitem__(self, key):
        """Implement ``del …[]``."""
        self.ary.__delitem__(key)
        self.writecount += 1
        if self.renderer:
            self.renderer.render(array=self.ary)
