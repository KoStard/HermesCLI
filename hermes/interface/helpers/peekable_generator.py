#! /usr/bin/env python3

"""
Implement iterate_while function and a peekable generator.
Allows easier branching in the processing of the generator.

This answers the question:
How can you pass a generator to another function, such that it consumes only part of it?
"""

from typing import Generator, TypeVar

T = TypeVar("T")


class PeekableGenerator:
    def __init__(self, generator: Generator[T, None, None]):
        self._generator = generator
        self._cache = []

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def peek(self):
        if not self._cache:
            self._cache.append(next(self._generator))
        return self._cache[0]

    def next(self):
        if self._cache:
            return self._cache.pop(0)
        return next(self._generator)


def iterate_while(
    peekable_generator: PeekableGenerator, condition
) -> Generator[T, None, None]:
    """
    Iterate over a peekable generator while condition is True.

    Args:
        peekable_generator: PeekableGenerator
        condition: Callable that takes one item and returns bool
    """

    try:
        while condition(peekable_generator.peek()):
            yield peekable_generator.next()
    except StopIteration:
        pass
