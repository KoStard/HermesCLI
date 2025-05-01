"""
Core command processing framework for Hermes interfaces.

Provides generic classes for defining, registering, parsing, and validating commands.
"""

from .command import Command, CommandSection, CommandRegistry
from .command_parser import CommandParser, CommandError, ParseResult
from .help_generator import CommandHelpGenerator

__all__ = [
    "Command",
    "CommandSection",
    "CommandRegistry",
    "CommandParser",
    "CommandError",
    "ParseResult",
    "CommandHelpGenerator",
]
