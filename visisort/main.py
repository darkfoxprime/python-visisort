
import renderable
import time
import sys
import random
import renderer
import threading
import synchronizer
import wx

def bubblesort(a):
    l = len(a)
    while l > 1:
        i = 0
        l -= 1
        while i < l:
            i += 1
            a1 = a[i-1]
            a2 = a[i]
            if a1 > a2:
                a[i-1] = a2
                a[i] = a1

def modified_bubblesort(a):
    l = len(a)
    i = 1
    while i < l:
        a1 = a[i-1]
        a2 = a[i]
        if a1 > a2:
            a[i-1] = a2
            a[i] = a1
            if i > 1:
                i -= 1
            else:
                i += 1
        else:
            i += 1

# `stride` is for use by shellsort
def insertionsort(a, stride=1,start=0):
    i = start+stride
    while i < len(a):
        x = a[i]
        j = i-stride
        while j>=start:
            y = a[j]
            if y <= x:
                break
            a[j+stride] = y
            j -= stride
        a[j+stride] = x
        i += stride

def shellsort(a):
    l = len(a)
    s = l
    while s > 1:
        s = s/2
        i = 0
        while i < s:
            insertionsort(a,s,i)
            i += 1

def binary_radixsort_lsb(a):
    l = len(a)
    max_bit = 1
    bits = 0
    while max_bit < l:
        max_bit *= 2
        bits += 1
    for bit in range(bits):
        first = [None,None]
        next = [None]*l
        i = l
        while i > 0:
            i -= 1
            b = (a[i] >> bit) & 1
            next[i], first[b] = first[b], i
        # i should be equal to 0 now
        for b in (0,1):
            j = first[b]
            while j is not None:
                next[j], j = i, next[j]
                i += 1
        # i should be equal to l now
        while i > 0:
            i -= 1
            # at this point, we know that a[i] is supposed to end up at a[next[i]]
            # so as long as i != next[i], we need to move something.
            # we need to keep track of where we started, so we use j to move around.
            #     jval, j = a[i], next[i]
            # while j is not i, swap a[j] with jval, and swap next[j] with j.
            # do the swaps all in one statement to avoid messing up interim indices.
            #     a[j], jval, next[j], j = jval, a[j], j, next[j]
            j = next[i]
            if j != i:
                jval = a[i]
                while j != i:
                    a[j], next[j], jval, j = jval, j, a[j], next[j]
                a[j], next[j] = jval, j

def quicksort(a, lo=None, hi=None):
    class EndOfPartition(BaseException): pass
    if lo is None:
        lo = 0
        hi = len(a)-1
##    import inspect
##    print "{0}quicksort(a, {1}, {2})".format(" "*len(inspect.stack()), lo, hi)
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
##                print " {0}exchange {1}[{2}] and {3}[{4}]".format(" "*len(inspect.stack()), i, ai, j, aj)
                a[i] = aj
                a[j] = ai
        except EndOfPartition,m:
            p = m.args[0]
            quicksort(a, lo, p-1)
            quicksort(a, p+1, hi)

class ImageUpdateSynchronizer(synchronizer.Synchronizer):
    def __init__(self, *args, **kwargs):
        super(ImageUpdateSynchronizer,self).__init__(*args, **kwargs)
        self.render_map = {}
    def map_renderer_to_image(self, renderer, image):
        self.render_map[renderer] = image
    def synchronized(self):
        for renderer in self.render_map:
            self.render_map[renderer].SetBitmap(renderer.image)

def run_sorting_method(method, initial, renderer, startup_cond):
    print "In run_sorting_method for " + method.__name__; sys.stdout.flush()
    print "Acquiring startup_cond for " + method.__name__; sys.stdout.flush()
    startup_cond.acquire()
    print "Waiting for startup_cond for " + method.__name__; sys.stdout.flush()
    startup_cond.wait()
    print "Releasing startup_cond for " + method.__name__; sys.stdout.flush()
    startup_cond.release()
    print "Running " + method.__name__; sys.stdout.flush()
    renderable_array = renderable.RenderableArray(initial, renderer)
    method(renderable_array)
    renderer.done()

def main():
    if len(sys.argv) != 2:
        print "Usage: {0} <arraysize>".format(sys.argv[0])
        sys.exit(0 if len(sys.argv) == 1 else 22)
    try:
        arraysize = int(sys.argv[1])
    except ValueError:
        print "Expected array size to be an integer, got {0!r}".format(sys.argv[1])
        sys.exit(22)

    methods = (
                bubblesort,
                modified_bubblesort,
                insertionsort,
                shellsort,
                binary_radixsort_lsb,
                quicksort
            )

    random_list = range(arraysize)
    #random.seed(0)
    random.shuffle(random_list)

    # create the UI.
    app = wx.App()
    # start out maximized so that we know that's the _largest_ we can make the frame.
    frame = wx.Frame(None, title = "Sorting Fun", style = wx.DEFAULT_FRAME_STYLE | wx.MAXIMIZE)
    frame_size = frame.GetSize()
    print "frame size is {0}x{1}".format(frame_size.width, frame_size.height)
    # loop columns from 1 to len(methods)
    # determine, based on frame_size, the size of the images for
    # that may columns.
    # record the size, rows, and columns that result in the largest image size.
    layout_image_size = 0
    layout_rows = 0
    layout_cols = 0
    for cols in range(1, 1+len(methods)):
        rows = (len(methods) + (cols-1)) / cols
        col_size = frame_size.width / cols
        row_size = frame_size.height / rows
        # pick the _smaller_ of the two sizes to use for the image size
        if col_size < row_size and col_size > layout_image_size:
            layout_image_size, layout_rows, layout_cols = col_size, rows, cols
        elif row_size < col_size and row_size > layout_image_size:
            layout_image_size, layout_rows, layout_cols = row_size, rows, cols
    # create the gridsizer
    sizer = wx.GridSizer(layout_cols, vgap=4, hgap=4)
    image_size = min(arraysize, layout_image_size - 4)

    threads = {}
    synchronizer = ImageUpdateSynchronizer()
    startup_cond = threading.Condition()

    for method in methods:
        print "Creating renderer for " + method.__name__; sys.stdout.flush()
        method_renderer = renderer.CircleImageRenderer(name=method.__name__, synchronizer=synchronizer, size=image_size)
        print "Creating image for " + method.__name__; sys.stdout.flush()
        method_image = wx.StaticBitmap(frame, bitmap=wx.NullBitmap, size=wx.Size(image_size, image_size))
        print "Adding renderer to synchronizer for " + method.__name__; sys.stdout.flush()
        synchronizer.map_renderer_to_image(method_renderer, method_image)
        print "Adding image to sizer for " + method.__name__; sys.stdout.flush()
        sizer.Add(method_image)
        print "Creating thread for " + method.__name__; sys.stdout.flush()
        threads[method.__name__] = threading.Thread(target=run_sorting_method, name=method.__name__, args=(method, random_list, method_renderer, startup_cond))

    for method in methods:
        print "Starting thread for " + method.__name__; sys.stdout.flush()
        threads[method.__name__].start()

    frame.SetSizerAndFit(sizer)
    frame.Centre()
    # finish creating the UI
    frame.Show()

    # give a bit of time for threads to start
    time.sleep(1)
    # then notify the start condition
    startup_cond.acquire()
    startup_cond.notifyAll()
    startup_cond.release()

    app.MainLoop()

if __name__ == '__main__':
    main()
