from typing import Dict, List, Optional, Type
import sys
import re
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
from hermes.chat_models.base import ChatModel
from hermes.context_providers.text_context_provider import TextContextProvider
from hermes.context_providers.append_context_provider import AppendContextProvider
from hermes.context_providers.update_context_provider import UpdateContextProvider
from hermes.context_providers.fill_gaps_context_provider import FillGapsContextProvider
from hermes.file_processors.base import FileProcessor
from hermes.prompt_builders.base import PromptBuilder
from hermes.chat_ui import ChatUI
from hermes.utils import file_utils
from hermes.history_builder import HistoryBuilder
from hermes.context_providers.base import ContextProvider
from hermes.config import HermesConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatApplication:
    def __init__(
        self,
        model: ChatModel,
        ui: ChatUI,
        file_processor: FileProcessor,
        prompt_builder_class: Type[PromptBuilder],
        context_provider_classes: List[Type[ContextProvider]],
        hermes_config: HermesConfig,
    ):
        self.model = model
        self.ui = ui
        self.history_builder = HistoryBuilder(prompt_builder_class, file_processor)

        # Instantiate and initialize context providers
        self.context_providers = [
            provider_class() for provider_class in context_provider_classes
        ]
        self.command_keys_map = {}
        for provider_class in context_provider_classes:
            command_keys = provider_class.get_command_key()
            if isinstance(command_keys, str):
                command_keys = [command_keys]
            for key in command_keys:
                key = key.strip()
                self.command_keys_map[key] = provider_class

        for provider in self.context_providers:
            provider.load_context_from_cli(hermes_config)
            self.history_builder.add_context(provider)

    def run(
        self,
        initial_prompt: Optional[str] = None,
    ):
        self.model.initialize()

        # Check if input or output is coming from a pipe
        is_input_piped = not sys.stdin.isatty()
        is_output_piped = not sys.stdout.isatty()

        if is_input_piped or is_output_piped:
            self.handle_non_interactive_input_output(
                initial_prompt, is_input_piped, is_output_piped
            )
            return

        # Interactive mode
        try:
            self.handle_interactive_mode(initial_prompt)
        except KeyboardInterrupt:
            print("\nChat interrupted. Exiting gracefully...")

    def handle_interactive_mode(self, initial_prompt):
        if any(isinstance(provider, (AppendContextProvider, UpdateContextProvider, FillGapsContextProvider)) and provider.file_path for provider in self.context_providers):
            # For special context providers, just make the first request and return
            self.make_first_request(initial_prompt)
            return

        if not self.make_first_request(initial_prompt):
            return

        while True:
            user_input = self.get_user_input()
            if user_input is None:
                return
            self.send_message_and_print_output(user_input)

    def get_user_input(self):
        while True:
            user_input = self.ui.get_user_input()
            user_input_lower = user_input.lower()

            if user_input_lower in ["exit", "quit", "q"]:
                return None
            elif user_input_lower == "/clear":
                self.clear_chat()
                continue
            elif user_input.startswith("/"):
                commands = re.finditer(r"(?:^|\s)(\/)(?:\w+\s)", user_input)
                command_start_indexes = [command.span(1)[1] for command in commands]
                full_commands = [
                    user_input[
                        start : (
                            command_start_indexes[index + 1]
                            if index < len(command_start_indexes) - 1
                            else len(user_input)
                        )
                    ]
                    for (index, start) in enumerate(command_start_indexes)
                ]

                for cmd in full_commands:
                    command, *args = cmd.strip().split(maxsplit=1)
                    if command in self.command_keys_map:
                        provider = self.command_keys_map[command]()
                        args_str = args[0] if args else ""
                        provider.load_context_from_string(args_str)
                        self.history_builder.add_context(provider)
                        self.ui.display_status(f"Context added for /{command}")
                    else:
                        self.ui.display_status(f"Unknown command: /{command}")
                continue

            return user_input

    def make_first_request(
        self,
        initial_prompt: Optional[str] = None,
    ):
        self.history_builder.clear_regular_history()
        if initial_prompt is not None:
            message = initial_prompt
        elif any(isinstance(provider, (AppendContextProvider, UpdateContextProvider, FillGapsContextProvider)) and provider.file_path for provider in self.context_providers):
            message = "Please process the provided context."
        else:
            message = self.get_user_input()
        
        if message is None:
            return False

        self.send_message_and_print_output(message)
        return True

    def handle_non_interactive_input_output(
        self, initial_prompt, is_input_piped, is_output_piped
    ):
        message = ""
        if initial_prompt:
            message = initial_prompt
        if is_input_piped:
            text_context_provider = TextContextProvider()
            text_context_provider.load_context_from_string(sys.stdin.read().strip())
            self.history_builder.add_context(text_context_provider)
        elif not initial_prompt:
            message = self.ui.get_user_input()

        response = self.send_message_and_print_output(message)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        before_sleep=before_sleep_log(logger, logging.INFO)
    )
    def _send_model_request(self, messages):
        return self.model.send_history(messages)

    def send_message_and_print_output(self, user_input):
        try:
            self.history_builder.add_message("user", user_input)
            messages = self.history_builder.build_messages()
            try:
                response = self.ui.display_response(self._send_model_request(messages))
                self.history_builder.add_message("assistant", response)
                self.apply_special_commands(response)
                return response
            except Exception as e:
                logger.error(f"Error during model request: {str(e)}")
                self.ui.display_status(f"An error occurred: {str(e)}")
                self.history_builder.pop_message()
        except KeyboardInterrupt:
            print()
            self.ui.display_status("Interrupted...")
            self.history_builder.pop_message()

    def apply_special_commands(self, content: str):
        for provider in self.context_providers:
            if isinstance(provider, (AppendContextProvider, UpdateContextProvider, FillGapsContextProvider)):
                if provider.file_path:
                    if isinstance(provider, AppendContextProvider):
                        file_utils.write_file(provider.file_path, "\n" + content, mode="a")
                        self.ui.display_status(f"Content appended to {provider.file_path}")
                    elif isinstance(provider, UpdateContextProvider):
                        file_utils.write_file(provider.file_path, content, mode="w")
                        self.ui.display_status(f"File {provider.file_path} updated")
                    elif isinstance(provider, FillGapsContextProvider):
                        original_content = file_utils.read_file_content(provider.file_path)
                        filled_content = self._fill_gaps(original_content, content)
                        file_utils.write_file(provider.file_path, filled_content, mode="w")
                        self.ui.display_status(f"Gaps filled in {provider.file_path}")

    def _fill_gaps(self, original_content: str, new_content: str) -> str:
        # Split the original content into lines
        original_lines = original_content.split('\n')

        # Find all gap markers and add indices
        gap_markers = []
        for i, line in enumerate(original_lines):
            if '<GapToFill>' in line:
                gap_markers.append(i)
                original_lines[i] = line.replace('<GapToFill>', f'<GapToFill index={len(gap_markers)}>')

        # Join the lines with added indices
        indexed_content = '\n'.join(original_lines)

        # Send the indexed content to the LLM (this part is handled elsewhere)

        # Extract new content for each gap
        new_content_blocks = re.findall(r'<NewGapContent index=(\d+)>(.*?)</NewGapContent>', new_content, re.DOTALL)

        # Replace gaps with new content
        for index, content in new_content_blocks:
            index = int(index)
            if index <= len(gap_markers):
                gap_line = gap_markers[index - 1]
                original_lines[gap_line] = original_lines[gap_line].split('<GapToFill')[0] + content.strip()
        # Join the lines back together
        return '\n'.join(original_lines)

    def clear_chat(self):
        self.model.initialize()
        self.history_builder.clear_regular_history()
        self.ui.display_status("Chat history cleared.")
