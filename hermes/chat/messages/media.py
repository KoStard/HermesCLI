from dataclasses import dataclass
from datetime import datetime

from hermes.chat.messages.base import Message
from hermes.utils.filepath import prepare_filepath


@dataclass(init=False)
class ImageUrlMessage(Message):
    """Class for messages that are image urls"""

    image_url: str

    def __init__(self, *, author: str, image_url: str, timestamp: datetime | None = None):
        super().__init__(author=author, timestamp=timestamp)
        self.image_url = image_url

    def get_content_for_user(self) -> str:
        return f"Image URL: {self.image_url}"

    def get_content_for_assistant(self) -> str:
        return self.image_url

    def to_json(self) -> dict:
        return {
            "type": "image_url",
            "image_url": self.image_url,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
        }

    @staticmethod
    def from_json(json_data: dict) -> "ImageUrlMessage":
        return ImageUrlMessage(
            author=json_data["author"],
            image_url=json_data["image_url"],
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
        )


@dataclass(init=False)
class ImageMessage(Message):
    """Class for messages that are images"""

    image_path: str

    IMAGE_EXTENSION_MAP = {
        "jpg": "jpeg",
    }

    def __init__(self, *, author: str, image_path: str, timestamp: datetime | None = None):
        super().__init__(author=author, timestamp=timestamp)
        self.image_path = prepare_filepath(image_path)

    def get_content_for_user(self) -> str:
        return f"Image: {self.image_path}"

    def get_content_for_assistant(self) -> str:
        return self.image_path

    def to_json(self) -> dict:
        return {
            "type": "image",
            "image_path": self.image_path,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
        }

    @staticmethod
    def from_json(json_data: dict) -> "ImageMessage":
        return ImageMessage(
            author=json_data["author"],
            image_path=json_data["image_path"],
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
        )


@dataclass(init=False)
class AudioFileMessage(Message):
    """Class for messages that are audio files"""

    audio_filepath: str

    def __init__(self, *, author: str, audio_filepath: str, timestamp: datetime | None = None):
        super().__init__(author=author, timestamp=timestamp)
        self.audio_filepath = prepare_filepath(audio_filepath)

    def get_content_for_user(self) -> str:
        return f"Audio: {self.audio_filepath}"

    def get_content_for_assistant(self) -> str:
        return self.audio_filepath

    def to_json(self) -> dict:
        return {
            "type": "audio",
            "audio_filepath": self.audio_filepath,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
        }

    @staticmethod
    def from_json(json_data: dict) -> "AudioFileMessage":
        return AudioFileMessage(
            author=json_data["author"],
            audio_filepath=json_data["audio_filepath"],
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
        )


@dataclass(init=False)
class VideoMessage(Message):
    """Class for messages that are videos"""

    video_filepath: str

    def __init__(self, *, author: str, video_filepath: str, timestamp: datetime | None = None):
        super().__init__(author=author, timestamp=timestamp)
        self.video_filepath = prepare_filepath(video_filepath)

    def get_content_for_user(self) -> str:
        return f"Video: {self.video_filepath}"

    def get_content_for_assistant(self) -> str:
        return self.video_filepath

    def to_json(self) -> dict:
        return {
            "type": "video",
            "video_filepath": self.video_filepath,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
        }

    @staticmethod
    def from_json(json_data: dict) -> "VideoMessage":
        return VideoMessage(
            author=json_data["author"],
            video_filepath=json_data["video_filepath"],
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
        )
