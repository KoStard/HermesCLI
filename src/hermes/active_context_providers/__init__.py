from .append_context_provider import AppendContextProvider
from .update_context_provider import UpdateContextProvider
from .fill_gaps_context_provider import FillGapsContextProvider

def get_all_active_context_providers():
    return [
        AppendContextProvider,
        UpdateContextProvider,
        FillGapsContextProvider,
    ]
