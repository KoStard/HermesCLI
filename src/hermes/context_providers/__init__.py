from .prompt_file_context_provider import PromptFileContextProvider
from .prefill_context_provider import PrefillContextProvider
from .url_context_provider import URLContextProvider
from .update_context_provider import UpdateContextProvider
from .file_context_provider import FileContextProvider
from .image_context_provider import ImageContextProvider
from .append_context_provider import AppendContextProvider
from .text_context_provider import TextContextProvider
from .fill_gaps_context_provider import FillGapsContextProvider
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
        UpdateContextProvider,
        FileContextProvider,
        ImageContextProvider,
        AppendContextProvider,
        TextContextProvider,
        FillGapsContextProvider,
        PromptContextProvider,
        EMLContextProvider,
        ClipboardContextProvider,
        LiveFileContextProvider,
    ]
