# SortableArray
#
# This is the base class for the sort visualizer.
# This class takes care of all the array-type stuff, and counts how many
# array accesses are made.

class SortableArray(object):
    def __init__(self, iterable=()):
        self.ary = list(iterable)
        self.resetStatistics()

    def resetStatistics(self):
        self.readcount = 0
        self.writecount = 0

    def __len__(self):
        return self.ary.__len__()

    def __nonzero__(self):
        return self.ary.__nonzero__()

    def __getitem__(self, key):
        value = self.ary.__getitem__(key)
        self.readcount += 1
        return value

    def ____missing__(self, key):
        return self.ary.__missing__(key)

    def __setitem__(self, key, value):
        self.ary.__setitem__(key, value)
        self.writecount += 1

    def __delitem__(self, key):
        self.ary.__delitem__(key)
        self.writecount += 1

    def __iter__(self):
        return self.ary.__iter__()

    def __reversed__(self):
        return self.ary.__reversed__()

    def __contains__(self):
        return self.ary.__contains__()
