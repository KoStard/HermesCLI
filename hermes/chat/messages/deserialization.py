from hermes.chat.messages.command import LLMRunCommandOutput
from hermes.chat.messages.text import TextMessage, InvisibleMessage, AssistantNotificationMessage
from hermes.chat.messages.text_generator import TextGeneratorMessage
from hermes.chat.messages.media import ImageUrlMessage, ImageMessage, AudioFileMessage, VideoMessage
from hermes.chat.messages.file import TextualFileMessage, EmbeddedPDFMessage
from hermes.chat.messages.url import UrlMessage
from hermes.chat.messages.thinking_and_response import ThinkingAndResponseGeneratorMessage


DESERIALIZATION_KEYMAP = {
    "llm_run_command_output": LLMRunCommandOutput.from_json,
    "text": TextMessage.from_json,
    "text_generator": TextGeneratorMessage.from_json,
    "invisible": InvisibleMessage.from_json,
    "image_url": ImageUrlMessage.from_json,
    "image": ImageMessage.from_json,
    "audio": AudioFileMessage.from_json,
    "video": VideoMessage.from_json,
    "pdf": EmbeddedPDFMessage.from_json,
    "textual_file": TextualFileMessage.from_json,
    "url": UrlMessage.from_json,
    "thinking_and_response_generator": ThinkingAndResponseGeneratorMessage.from_json,
    "assistant_notification": AssistantNotificationMessage.from_json,
}