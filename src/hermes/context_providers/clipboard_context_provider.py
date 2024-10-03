import pyperclip
from typing import List
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder

class ClipboardContextProvider(ContextProvider):
    def __init__(self):
        self.clipboard_content: str = ""

    @staticmethod
    def add_argument(parser):
        parser.add_argument('--clipboard', action='store_true', help='Include clipboard content in the context')

    @staticmethod
    def get_help() -> str:
        return 'Include clipboard content in the context'

    def load_context_from_cli(self, args):
        if args.clipboard:
            print("Loading clipboard content...")
            self.clipboard_content = pyperclip.paste()

    def load_context_from_string(self, _):
        print("Loading clipboard content...")
        self.clipboard_content = pyperclip.paste()

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        if self.clipboard_content:
            prompt_builder.add_text("Clipboard Content", self.clipboard_content)

    @staticmethod
    def get_command_key() -> List[str]:
        return ["clipboard"]