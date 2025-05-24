"""
Messages are what the participant sends to the other participant through the engine
Some messages are commands, they might not go through to the other participant, maybe they are for the engine itself.
Imagine using Telegram or some other messaging app. What you can add and press Send is what a message is.
With difference that you can send multiple messages at once.
"""

from hermes.chat.messages.base import Message
from hermes.chat.messages.command import LLMRunCommandOutput
from hermes.chat.messages.deserialization import DESERIALIZATION_KEYMAP
from hermes.chat.messages.file import EmbeddedPDFMessage, TextualFileMessage
from hermes.chat.messages.media import AudioFileMessage, ImageMessage, ImageUrlMessage, VideoMessage
from hermes.chat.messages.text import AssistantNotificationMessage, InvisibleMessage, TextMessage
from hermes.chat.messages.text_generator import TextGeneratorMessage
from hermes.chat.messages.thinking_and_response import ThinkingAndResponseGeneratorMessage
from hermes.chat.messages.url import UrlMessage

__all__ = [
    "Message",
    "TextMessage",
    "InvisibleMessage",
    "AssistantNotificationMessage",
    "TextGeneratorMessage", 
    "ThinkingAndResponseGeneratorMessage",
    "ImageUrlMessage",
    "ImageMessage",
    "AudioFileMessage",
    "VideoMessage",
    "TextualFileMessage",
    "EmbeddedPDFMessage",
    "LLMRunCommandOutput",
    "UrlMessage",
    "DESERIALIZATION_KEYMAP",
]