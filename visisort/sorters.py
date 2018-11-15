"""
This module holds the sorting algorithms implemented for visualization.

Sorting algorithms are implemented in subclasses of the
``MicroThreadedSortAlgorithm`` abstract superclass.  Because of the
restrictions of a microthreaded implementation, the superclass itself
provides almost no functionality to the underlying implementations,
other than actually initializing the array to be sorted.

Each specific sort algorithm class must implement a ``sort()``
generator method, which runs the desired sort algorithm and ``yield``s
a ``SortOperation`` object each time a read or write operation is done
on the array, and once more when the sort algorithm completes.

Sort algorithms should all accept the ``lo`` and ``hi`` keyword
parameters to establish the lower and upper bounds of the portion of
the array to be sorted - for example, a ``lo`` of ``2`` and a ``hi``
of ``5`` means the four elements ``[2]``, ``[3]``, ``[4]``, ``[5]``
will be sorted.
"""


class SortOperation(object):
    """
    The general superclass for sort operations.

    The actual operations are subclasses of this.

    Subclasses must override the ``__init__`` method itself!
    """

    def __init__(self):
        """
        Initialize the object.

        Subclasses must override this!
        """
        raise NotImplementedError


class ReadOperation(SortOperation):
    """
    A read operation.

    The ``index`` attribute indicates the position in the array which
    was read.
    """

    def __init__(self, index):
        """Initialize the object."""
        self.index = index


class WriteOperation(SortOperation):
    """
    A write operation.

    The ``index`` attribute indicates the position in the array which
    was written, the ``value`` attribute holds the value that was
    written into the array, and the ``array`` attribute holds the entire
    contents of the array.
    """

    def __init__(self, index, value, array):
        """Initialize the object."""
        self.index = index
        self.value = value
        self.array = array


class SortComplete(SortOperation):
    """
    The sort is complete.

    The ``array`` attribute holds the final contents of the array.
    """

    def __init__(self, array):
        """Initialize the object."""
        self.array = array


class MicroThreadedSortAlgorithm(object):
    """
    The general superclass of the MicroThreaded sort algorithms.

    Each subclass must implement its own ``sort`` method.
    """

    def __init__(self, array, **kwargs):
        """
        Instantiate the sort algorithm.

        Every algorithm obviously needs an array to operate on.
        The array is duplicated to ensure we're operating on our
        own independent version of the array.

        All other options to an algorithm would be passed in
        through keyword arguments.  Unknown keyword arguments are
        silently ignored.

        subclasses should make sure that, if they need a custom
        ``__init__`` method, the first thing that method does is

            super().__init__(array, **kwargs)
        """
        self.array = array[:]

    def sort(self, **kwargs):
        """
        Perform the sort operation itself.

        This method must be overridden by subclasses.

        In order to measure sort algorithms against each other,
        the sort algorithm must use ``yield`` after certain
        operations in order to keep in step with other sort
        algorithms.

        *   After reading from the array, yield a ``ReadOperation``
            instance indicating the index into the array that was just
            read.
        *   After writing to the array, yield a ``WriteOperation``
            instance, providing the index into the array that was
            written to, the value written at that index, and the
            array itself.
        *   When the sort is complete, yield a ``SortComplete``
            instance with the final contents of the array.

        The options to the sort operation are passed in through keyword
        arguments, and unknown arguments are silently ignored.

        It is recommended that all sort algorithms should recognize
        the following minimum set of keyword arguments:
        *   ``lo``
            -   The lowest index of the portion of the array to
                sort.  This defaults to ``0``.
        *   ``hi``
            -   The highest index of the portion of the array to
                sort.  This defaults to the length of the array - 1.
        """
        raise NotImplementedError


class BubbleSortAlgorithm(MicroThreadedSortAlgorithm):
    """
    Implements the "Bubble Sort" algorithm.

    This is the most simplistic sorting algorithm, which "bubbles"
    higher values towards the end of the array.
    """

    def sort(self, **kwargs):
        """Perform a bubble sort."""
        lo = kwargs.pop('lo', 0)
        hi = kwargs.pop('hi', len(self.array) - 1)

        top = hi - 1
        while top > lo:
            idx = lo
            while idx <= top:
                idx += 1
                a1 = self.array[idx - 1]
                yield ReadOperation(idx - 1)
                a2 = self.array[idx]
                yield ReadOperation(idx)
                if a1 > a2:
                    self.array[idx - 1] = a2
                    yield WriteOperation(idx - 1, a2, self.array)
                    self.array[idx] = a1
                    yield WriteOperation(idx, a1, self.array)
            top -= 1

        yield SortComplete(self.array)


class ReadOptimizedBubbleSortAlgorithm(MicroThreadedSortAlgorithm):
    """
    Implements the "Bubble Sort" algorithm with read optimizations.

    This is the most simplistic sorting algorithm, which "bubbles"
    higher values towards the end of the array.  This slightly
    optimizes the traditional bubble sort by reducing the number of
    times the array is read.
    """

    def sort(self, **kwargs):
        """Perform a bubble sort."""
        lo = kwargs.pop('lo', 0)
        hi = kwargs.pop('hi', len(self.array) - 1)

        top = hi - 1
        while top > lo:
            idx = lo
            a1 = self.array[idx]
            yield ReadOperation(idx)
            while idx <= top:
                idx += 1
                a2 = self.array[idx]
                yield ReadOperation(idx)
                if a1 > a2:
                    self.array[idx - 1] = a2
                    yield WriteOperation(idx - 1, a2, self.array)
                    self.array[idx] = a1
                    yield WriteOperation(idx, a1, self.array)
                else:
                    a1 = a2
            top -= 1

        yield SortComplete(self.array)


class InsertionSortAlgorithm(MicroThreadedSortAlgorithm):
    """
    Implements the "Insertion Sort" algorithm.

    Insertion Sort loops through each value after the first in the
    range to be sorted and inserts it into the appropriate location
    in the part of the array that has been sorted so far.
    """

    def sort(self, **kwargs):
        """
        Sort the array using the "Insertion Sort" algorithm.

        The ``sort`` method takes one additional parameter for
        convenience in the later implementation of the Shell Sort:

        *   ``stride``
            -   The delta between subsequent values to sort.  By
                default, ``stride`` is equal to ``1``, which means each
                value is sorted.  If ``stride`` were equal to ``2``,
                then every other value, starting at ``lo``, would be
                sorted.
        """
        lo = kwargs.pop('lo', 0)
        hi = kwargs.pop('hi', len(self.array) - 1)
        stride = kwargs.pop('stride', 1)

        idx = lo + stride
        while idx <= hi:
            a1 = self.array[idx]
            yield ReadOperation(idx)
            ins_pt = idx - stride
            while ins_pt >= lo:
                a2 = self.array[ins_pt]
                yield ReadOperation(ins_pt)
                if a2 <= a1:
                    break
                self.array[ins_pt + stride] = a2
                yield WriteOperation(ins_pt + stride, a2, self.array)
                ins_pt -= stride
            idx += stride

        yield SortComplete(self.array)


class ShellSortAlgorithm(MicroThreadedSortAlgorithm):
    """Implements the "Shell Sort" algorithm."""

    def sort(self, **kwargs):
        """Sort the array using the "Shell Sort" algorithm."""
        lo = kwargs.pop('lo', 0)
        hi = kwargs.pop('hi', len(self.array) - 1)

        stride = hi - lo + 1
        while stride > 1:
            stride //= 2
            idx = stride
            while idx > 0:
                idx -= 1
                for op in super(ShellSortAlgorithm, self).sort(
                            lo=lo + idx,
                            hi=hi,
                            stride=stride,
                        ):
                    if not isinstance(op, SortComplete):
                        yield op

        yield SortComplete(self.array)


class QuickSortAlgorithm(MicroThreadedSortAlgorithm):
    """Implements the "Quick Sort" algorithm."""

    def sort(self, **kwargs):
        """Sort the array using the "Quick Sort" algorithm."""
        lo = kwargs.pop('lo', 0)
        hi = kwargs.pop('hi', len(self.array) - 1)
        sub_sort = kwargs.pop('sub_sort', False)

        # partition the space around the value at the lowest index.
        lo_idx = lo
        hi_idx = hi
        p = self.array[lo]
        yield ReadOperation(lo)
        while lo_idx < hi_idx:
            while lo_idx < hi_idx:
                a1 = self.array[lo_idx]
                yield ReadOperation(lo_idx)
                if a1 >= p:
                    break
                lo_idx += 1
            while lo_idx < hi_idx:
                a2 = self.array[hi_idx]
                yield ReadOperation(hi_idx)
                if a2 <= p:
                    break
            if lo_idx < hi_idx:
                self.array[lo_idx] = a2
                yield WriteOperation(lo_idx, a2, self.array)
                self.array[hi_idx] = a1
                yield WriteOperation(hi_idx, a1, self.array)
        # recursively sort the low partition of the space
        self.sort(lo=lo, hi=hi_idx - 1, sub_sort=True)
        # recursively sort the high partition of the space
        self.sort(lo=hi_idx + 1, hi=hi, sub_sort=True)

        # check if we're done with the main sort call so we can
        # yield the ``SortComplete`` operation.
        if not sub_sort:
            yield SortComplete(self.array)
