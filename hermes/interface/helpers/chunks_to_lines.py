from collections.abc import Generator


def chunks_to_lines(chunks: Generator[str, None, None]) -> Generator[str, None, None]:
    buffer = ""
    for chunk in chunks:
        buffer += chunk
        while "\n" in buffer:
            yield buffer[: buffer.index("\n")] + "\n"
            buffer = buffer[buffer.index("\n") + 1 :]
    if buffer:
        yield buffer
