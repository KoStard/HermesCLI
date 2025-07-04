from collections.abc import Generator
from typing import Generic, TypeVar

GeneratorItemType = TypeVar("GeneratorItemType")


class RecordingGenerator(Generic[GeneratorItemType]):
    def __init__(self, original_generator: Generator[GeneratorItemType, None, None]):
        self.original_generator: Generator[GeneratorItemType, None, None] = original_generator
        self.collected_values = []

    def __iter__(self):
        return self

    def __next__(self) -> GeneratorItemType:
        value = next(self.original_generator)
        self.collected_values.append(value)
        return value
