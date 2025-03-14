import sys


class OverridingPrinter:
    def __init__(self, texts: list[str]):
        self.texts = texts
        self.index = 0
        self.max_length = max(len(text) for text in self.texts)

    def print_next(self, go_to_last_line: bool = False):
        if self.index > 0:
            if go_to_last_line:
                sys.stdout.write("\033[A\r")
            else:
                sys.stdout.write("\r")
        sys.stdout.write(self.texts[self.index])
        sys.stdout.write(" " * (self.max_length - len(self.texts[self.index])))
        sys.stdout.flush()
        self.index += 1
