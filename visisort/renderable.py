# SortableArray
#
# This is the base class for the sort visualizer.
# This class takes care of all the array-type stuff, and counts how many
# array accesses are made.

from sortable import SortableArray
class RenderableArray(SortableArray):
    def __init__(self, iterable=(), renderer=None):
        super(RenderableArray, self).__init__(iterable)
        self.renderer = renderer
        self.renderer.render(array = self.ary)

    def __getitem__(self, key):
        value = self.ary.__getitem__(key)
        self.readcount += 1
        if self.renderer:
            self.renderer.render(read_index=key, array=self.ary, read_count=self.readcount)
        return value

    def ____missing__(self, key):
        return self.ary.__missing__(key)

    def __setitem__(self, key, value):
        self.ary.__setitem__(key, value)
        self.writecount += 1
        if self.renderer:
            self.renderer.render(write_index=key, array=self.ary, write_count=self.writecount)

    def __delitem__(self, key):
        self.ary.__delitem__(key)
        self.writecount += 1
        if self.renderer:
            self.renderer.render(array=self.ary)

    def __iter__(self):
        return self.ary.__iter__()

    def __reversed__(self):
        return self.ary.__reversed__()

    def __contains__(self):
        return self.ary.__contains__()
