"""Implements the main ``visisort`` application."""

import sys
import random

import visisort.sorters


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

    sorters = (
                visisort.sorters.BubbleSortAlgorithm,
                visisort.sorters.ReadOptimizedBubbleSortAlgorithm,
                visisort.sorters.InsertionSortAlgorithm,
                visisort.sorters.ShellSortAlgorithm,
                visisort.sorters.QuickSortAlgorithm,
            )

    random_list = list(range(arraysize))
    random.shuffle(random_list)


if __name__ == '__main__':
    main()
