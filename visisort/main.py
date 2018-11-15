"""Implements the main ``visisort`` application."""

import visisort.renderable
import time
import sys
import random
import visisort.renderer
import threading
import visisort.synchronizer
import wx
import inspect
import wx.lib.statbmp


def bubblesort(a):
    """Sort the array `a` using the "bubble sort" method."""
    arraysize = len(a)
    while arraysize > 1:
        i = 0
        arraysize -= 1
        while i < arraysize:
            i += 1
            a1 = a[i - 1]
            a2 = a[i]
            if a1 > a2:
                a[i - 1] = a2
                a[i] = a1


def modified_bubblesort(a):
    """Sort the array `a` using my modified "bubble sort" method."""
    arraysize = len(a)
    i = 1
    while i < arraysize:
        a1 = a[i - 1]
        a2 = a[i]
        if a1 > a2:
            a[i - 1] = a2
            a[i] = a1
            if i > 1:
                i -= 1
            else:
                i += 1
        else:
            i += 1


def insertionsort(a, stride=1, start=0):
    """
    Sort the array `a` using the "Insertion Sort" method.

    `stride` and `start` are used by the Shell Sort sorting method.
    """
    i = start + stride
    while i < len(a):
        x = a[i]
        j = i - stride
        while j >= start:
            y = a[j]
            if y <= x:
                break
            a[j + stride] = y
            j -= stride
        a[j + stride] = x
        i += stride


def shellsort(a):
    """
    Sort the array `a` using the "Shell Sort" method.

    This makes use of the `insertionsort()` method above.
    """
    arraysize = len(a)
    s = arraysize
    while s > 1:
        s = s // 2
        i = 0
        while i < s:
            insertionsort(a, s, i)
            i += 1


def binary_radixsort_lsb(a):
    """
    Sort the array `a` using the "Radix Sort" method.

    Specifically, this uses a Base 2 Radix sort starting from the
    least-significant-bit of each value.
    """
    arraysize = len(a)
    max_bit = 1
    bits = 0
    while max_bit < arraysize:
        max_bit *= 2
        bits += 1
    for bit in range(bits):
        first = [None, None]
        next = [None] * arraysize
        i = arraysize
        while i > 0:
            i -= 1
            b = (a[i] >> bit) & 1
            next[i], first[b] = first[b], i
        # i should be equal to 0 now
        for b in (0, 1):
            j = first[b]
            while j is not None:
                next[j], j = i, next[j]
                i += 1
        # i should be equal to arraysize now
        while i > 0:
            i -= 1
            # at this point, we know that a[i] is supposed to end up at
            # a[next[i]], so as long as i != next[i], we need to move
            # something.
            #
            # we need to keep track of where we started, so we use j to move
            # around.
            #     jval, j = a[i], next[i]
            # while j is not i, swap a[j] with jval, and swap next[j] with j.
            # do the swaps all in one statement to avoid messing up interim
            # indices.
            #     a[j], jval, next[j], j = jval, a[j], j, next[j]
            j = next[i]
            if j != i:
                jval = a[i]
                while j != i:
                    a[j], next[j], jval, j = jval, j, a[j], next[j]
                a[j], next[j] = jval, j


def quicksort(a, lo=None, hi=None):
    """
    Sort the array `a` using the "Quick Sort" method.

    `lo` and `hi` are the bounds of the array to sort, used by quicksort's
    recursive self-invocations.
    """
    class EndOfPartition(BaseException):
        pass
    if lo is None:
        lo = 0
        hi = len(a) - 1
##    print("{0}quicksort(a, {1}, {2})".format(
##                " " * len(inspect.stack()),
##                lo,
##                hi
##            ))
    if lo < hi:
        try:
            pivot = a[lo]
##            print " {0}pivot = {1}".format(" "*len(inspect.stack()), pivot)
            i = lo
            j = hi
            while True:
                while i < j:
                    ai = a[i]
                    if ai >= pivot:
                        break
                    i += 1
                while i < j:
                    aj = a[j]
                    if aj <= pivot:
                        break
                    j -= 1
                if i >= j:
                    raise EndOfPartition(j)
                a[i] = aj
                a[j] = ai
        except EndOfPartition as partition:
            p = partition.args[0]
            quicksort(a, lo, p - 1)
            quicksort(a, p + 1, hi)


class ImageUpdateSynchronizer(visisort.synchronizer.Synchronizer):
    """
    A ``Synchronizer`` that keeps images up to date.

    Each image is associated with a ``renderer``.  Whenever the Synchronizer is
    in sync, each renderer's image will be copied to its associated target
    image.
    """

    def __init__(self, wx, *args, **kwargs):
        """Initialize the instance."""
        super(ImageUpdateSynchronizer, self).__init__(*args, **kwargs)
        self.wx = wx
        self.render_map = {}

    def map_renderer_to_image(self, renderer, image):
        """Add a mapping of a `renderer` to an `image`."""
        self.render_map[renderer] = image

    def synchronized(self):
        """
        Trigger a call to `synchronize.bitmaps`.

        Called by the parent ``Synchronizer`` instance when the sorting
        methods synchronize.
        """
        self.wx.CallAfter(self.synchronize_bitmaps)

    def synchronize_bitmaps(self):
        """
        Copy the rendered images into the target images.

        Called (indirectly) by `synchronized` via the WX event loop.
        """
        print("ImageUpdateSynchronizer running synchronize_bitmaps", flush=True)
        for image_renderer in self.render_map:
            if image_renderer.image:
                self.render_map[image_renderer].SetBitmap(image_renderer.image)


def run_sorting_method(method, initial, renderer, synchronizer, wx, startup_cond):
    """
    Run a particular sorting method.

    * `method` holds the function that performs the sort.
    * `initial` holds the initial contents of the array.
    * `renderer` is the renderer to use.
    * `startup_cond` is the ``Condition`` variable that gates the startup of
      the sort methods.
    """
    class CallAfterRenderer(visisort.renderer.SynchronizedRenderer):
        def __init__(self, **kwargs):
            self.real_renderer = kwargs.pop('renderer')
            self.wx = kwargs.pop('wx')
            super(CallAfterRenderer, self).__init__(**kwargs)

        def update(self, *args, **kwargs):
            (
                self.real_renderer.read_index,
                self.real_renderer.write_index,
                self.real_renderer.read_count,
                self.real_renderer.write_count,
                self.real_renderer.array,
            ) = (
                self.read_index,
                self.write_index,
                self.read_count,
                self.write_count,
                self.array,
            )
            #print("CallAfterRenderer[{0}] running update".format(self.name), flush=True)
            self.wx.CallAfter(self.real_renderer.update, *args, **kwargs)
            super(CallAfterRenderer, self).update(*args, **kwargs)
    print("In run_sorting_method for {0}".format(method.__name__))
    sys.stdout.flush()
    print("Acquiring startup_cond for {0}".format(method.__name__))
    sys.stdout.flush()
    startup_cond.acquire()
    print("Waiting for startup_cond for {0}".format(method.__name__))
    sys.stdout.flush()
    startup_cond.wait()
    print("Releasing startup_cond for {0}".format(method.__name__))
    sys.stdout.flush()
    startup_cond.release()
    print("Running {0}".format(method.__name__))
    sys.stdout.flush()
    renderable_array = visisort.renderable.RenderableArray(
                initial,
                CallAfterRenderer(
                    name=renderer.name,
                    synchronizer=synchronizer,
                    renderer=renderer,
                    wx=wx
                ),
            )
    method(renderable_array)
    renderer.done()


def main():
    """Run the main ``visisort`` program."""
    if len(sys.argv) != 2:
        print("Usage: {0} <arraysize>".format(sys.argv[0]))
        sys.exit(0 if len(sys.argv) == 1 else 22)
    try:
        arraysize = int(sys.argv[1])
    except ValueError:
        print("Expected array size to be an integer, got {0!r}".format(
            sys.argv[1]))
        sys.exit(22)

    methods = (
                bubblesort,
                modified_bubblesort,
                insertionsort,
                shellsort,
                binary_radixsort_lsb,
                quicksort
            )

    random_list = list(range(arraysize))
##    random.seed(0)
    random.shuffle(random_list)

    # create the UI.
    app = wx.App()
    # start out maximized so that we know that's the _largest_ we can make the
    # frame.
    frame = wx.Frame(None, title="Sorting Fun",
                     style=wx.DEFAULT_FRAME_STYLE | wx.MAXIMIZE)
    frame.Show()
    frame.Maximize(True)
    frame_size = frame.GetSize()
    print("frame size is {0}x{1}".format(frame_size.width, frame_size.height))
    # loop columns from 1 to len(methods)
    # determine, based on frame_size, the size of the images for
    # that may columns.
    # record the size, rows, and columns that result in the largest image size.
    layout_image_size = 0
    layout_rows = 0
    layout_cols = 0
    for cols in range(1, 1 + len(methods)):
        rows = (len(methods) + (cols - 1)) / cols
        col_size = frame_size.width / cols
        row_size = frame_size.height / rows
        # pick the _smaller_ of the two sizes to use for the image size
        if col_size < row_size and col_size > layout_image_size:
            layout_image_size, layout_rows, layout_cols = col_size, rows, cols
        elif row_size < col_size and row_size > layout_image_size:
            layout_image_size, layout_rows, layout_cols = row_size, rows, cols
    assert layout_rows > 0  # stop pyflake from complaining about unused var
    # create the gridsizer
    print("layout_image_size={0!r}".format(layout_image_size))
    sizer = wx.GridSizer(layout_cols, vgap=4, hgap=4)
    image_size = min(arraysize, layout_image_size - 4)
    print("image_size={0!r}".format(image_size))

    threads = {}
    synchronizer = ImageUpdateSynchronizer(wx)
    startup_cond = threading.Condition()

    for method in methods:
        print("Creating renderer for {0}".format(method.__name__), flush=True)
        method_renderer = visisort.renderer.CircleImageRenderer(
            name=method.__name__, size=image_size)
        print("Creating image for {0}".format(method.__name__), flush=True)
        method_image = wx.lib.statbmp.GenStaticBitmap(
            frame, ID=-1, bitmap=wx.NullBitmap, size=wx.Size(image_size, image_size))
        print("Mapping renderer to image in ImageUpdateSynchronizer", flush=True)
        synchronizer.map_renderer_to_image(method_renderer, method_image)
        print("Adding image to sizer for {0}".format(
            method.__name__), flush=True)
        sizer.Add(method_image)
        print("Creating thread for {0}".format(method.__name__), flush=True)
        threads[method.__name__] = threading.Thread(
                target=run_sorting_method,
                name=method.__name__,
                args=(method, random_list, method_renderer,
                      synchronizer, wx, startup_cond)
            )

    for method in methods:
        print("Starting thread for {0}".format(method.__name__))
        sys.stdout.flush()
        threads[method.__name__].start()

    frame.SetSizerAndFit(sizer)
    frame.Centre()

    # give a bit of time for threads to start
    time.sleep(1)
    # then notify the start condition
    startup_cond.acquire()
    startup_cond.notifyAll()
    startup_cond.release()

    app.MainLoop()


if __name__ == '__main__':
    main()
