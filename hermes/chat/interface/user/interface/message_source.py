from enum import Enum


class MessageSource(Enum):
    TERMINAL = "terminal"
    CLI = "cli"
    SPEECH = "speech"
