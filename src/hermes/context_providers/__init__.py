from .prompt_file_context_provider import PromptFileContextProvider
from .prefill_context_provider import PrefillContextProvider
from .url_context_provider import URLContextProvider
from .file_context_provider import FileContextProvider
from .image_context_provider import ImageContextProvider
from .text_context_provider import TextContextProvider
from .prompt_context_provider import PromptContextProvider
from .eml_context_provider import EMLContextProvider
from .clipboard_context_provider import ClipboardContextProvider
from .live_file_context_provider import LiveFileContextProvider
from .base import ContextProvider, LiveContextProvider

def get_all_context_providers():
    return [
        PromptFileContextProvider,
        PrefillContextProvider,
        URLContextProvider,
        FileContextProvider,
        ImageContextProvider,
        TextContextProvider,
        PromptContextProvider,
        EMLContextProvider,
        ClipboardContextProvider,
        LiveFileContextProvider,
    ]
