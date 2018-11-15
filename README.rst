visisort is Yet Another Visible Sort program.

***Needs to be reworked!***

# Architecture

This is a *non-threaded* architecture:  Because the GUI operations all
need to run in the primary thread, including image generation, which was
the requirement driving the use of multiple threads, a threaded
architecture becomes overly complex without actually allowing the heavy
workload to be distributed among threads.

Therefore, each sorting algorithm will be set up as a *generator*:
Whenever it does an operation that warrants synchronizing with the other
algorithms (meaning a read or write operation on the array being
sorted), it uses ``yield`` to inform the controller what operation was
done and any additional information about the operation that is
required.  The controller takes the information that was ``yield``ed to
it in order to trigger the update of the image associated with the
sorting algorithm.

When the sort is complete, the generator function finishes, the
``GeneratorExit`` exception is raised in the controller, which then
removes that sorting algorithm from the active list and does the final
update of the sorting algorithm's associated image.

This is apparently known as "MicroThreading".

# Organization

## Sorting Algorithms

The sorting algorithms will all be implemented as subclasses of
``SortAlgorithm``.  Unfortunately, because they are being implemented
as generator functions, there's no way to generalize the MicroThreading
aspect, so the subclassing will really only be a way to identify and
generalize the top level API.

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

            * After reading from the array, yield a tuple of
              ``(sorters.READ, `` *index* ``)``, where *index*
              is the index into the array that was just read.
            * After writing to the array, yield a tuple of
              ``(sorters.WRITE, `` *index* ``, self.array)``,
              where *index* is the index into the array that was
              just written to.  The entire array itself is also passed.
            * When the sort is complete, yield a final tuple of
              ``(sorters.DONE, self.array)``, then exit the method.

            Once again, the options to the sort operation are passed
            in through keyword arguments, and unknown arguments are
            silently ignored.

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

The sorting algorithm classes will all be gathered into a ``sorters``
module, which will also define the constants representing the operation
values ``yield``ed by the ``sort`` methods:

*   ``READ`` is yielded after a read operation, along with the index
    into the array that was read;
*   ``WRITE`` is yielded after a write operation, along with the index
    into the array that was written to *and* the array contents; and
*   ``DONE`` is yielded after the sort is complete, along with the array
    contents.

## Visualizations

The visualization methods will be implemented as subclasses of
``Visualizer``.  The public API to the ``Visualizer`` family of classes
consists of the initialization of the visualizer and the ``render``
method.

The initialization has one required argument among all the visualizer
classes:

*   ``name``
    -   The name of the sorting algorithm associated with this
        visualizer.

Other arguments may be required by specific visualizer classes.

The ``render`` method is used to render the actual operation of the
algorithm.  It takes any (or all) of the following optional keyword
arguments:

*   ``array``
    -   The contents of the array, if it has changed.
*   ``read_index``
    -   The index into the array that was just read, if any.  If
        ``None``, it is assumed that no read operation has taken place
        since the last call to ``render``.
*   ``write_index`
    -   The index into the array that was just written to, if any.
        Similar to ``read_index``, if this is ``None``, then it is
        assumed that no write operation has taken place since the last
        call to ``render``.
*   ``read_count``
    -   The number of times a read operation has taken place.  If
        ``None``, then the  read count is not updated and will keep
        the last value that was provided.
*   ``write_count``
    -   The number of times a write operation has taken place.  If
        ``None``, then the write count is not updated and will keep
        the last value that was provided.

### Text Output Visualizers

Two simple text output visualizers are implemented:

*   ``SummarizingVisualizer`` waits until the sorting algorithm is
    done, then reports how long it ran and how many read and write
    operations it performed.

*   ``WriteTrackingVisualizer`` is a subclass of
    ``SummarizingVisualizer``, but also reports the contents of the
    array each time a write operation occurs.

### Image Production Visualizers

The rest of the visualizers are the "meat" of the application.  They
each take the information provided to the ``render`` method and use it
to render the visualized array into an image.

By default, these visualizers create their own image.  Instead, however,
they can be provided an image and told what portion of that image to
use to render their visualization.

The superclass for all of these visualizers is the ``ImageVisualizer``
class.  It implements the ``render`` method to accept the sorting
information and calls helper methods to render that information into
the provided image:  ``render_background``, which clears the background
to the appropriate color and displays the sorting algorithm's name;
``render_indices``, which displays the read and write indices, if any;
and ``render_data``, which displays the content of the array.  In the
``ImageVisualizer`` superclass, these methods are all unimplemented,
and must be overridden by subclasses.

The following image visualizers are implemented:

*   ``ScatterGraphVisualizer`` renders the contents of the array as a
    straight-forward scatter graph: points are rendered from left to
    right corresponding to the array indices from low to high, and
    from bottom to top corresponding to the values stored in the array
    from low to high, respectively.  The color of each point gives an
    indication of how close or far the value is from being correct:
    white means the value is in the correct place, green means it's
    close to correct, and red means it's as far from being correct as
    possible.

    The read and write indices, if they exist, are rendered as vertical
    lines behind the graph in the corresponding horizontal location: a
    dark gray line for the read index and a medium gray line for the
    write index.

*   ``SpiralGraphVisualizer`` renders the array such that a perfectly
    sorted array forms a counterclockwise spiral, and unsorted values
    are bounded by a circle centered on the spiral.  The read and write
    indices are rendered as lines radiating from the center of the
    spiral to the edge of the bounding circle.

## Visualization Controller

The visualization controller is the engine that drives the application.
It receives the updates from each sorting algorithm, renders those
updates using one or more visualizers, then displays the results from
the visualizer or visualizers in the application window.
