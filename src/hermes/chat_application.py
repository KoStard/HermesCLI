import argparse
from typing import Dict, List, Optional, Type, Set
import sys
import re
import logging
from argparse import Namespace
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
logger = logging.getLogger(__name__)


class ChatApplication:
    def __init__(
        self,
        model: ChatModel,
        ui: ChatUI,
        file_processor: FileProcessor,
        prompt_builder_class: Type[PromptBuilder],
        context_provider_classes: List[Type[ContextProvider]],
        args: argparse.Namespace,
    ):
        self.model = model
        self.ui = ui
        self.history_builder = HistoryBuilder(prompt_builder_class, file_processor)
        self.has_input = False

        logger.info(f"Initializing with model: {type(model).__name__}")
        logger.info(f"Using file processor: {type(file_processor).__name__}")
        logger.info(f"Using prompt builder: {prompt_builder_class.__name__}")

        self.command_keys_map = {}
        for provider_class in context_provider_classes:
            command_keys = provider_class.get_command_key()
            if isinstance(command_keys, str):
                command_keys = [command_keys]
            for key in command_keys:
                key = key.strip()
                self.command_keys_map[key] = provider_class

        self._initialize_context_providers(args)

        logger.debug(
            f"Initialized {len(self.history_builder.context_providers)} context providers"
        )
        logger.debug("ChatApplication initialization complete")

    def _initialize_context_providers(self, args: argparse.Namespace):
        for key, value in vars(args).items():
            if key in self.command_keys_map and value is not None:
                self._initialize_context_provider(key, args)

    def _initialize_context_provider(
        self,
        provider_key: str,
        args: argparse.Namespace,
    ):
        provider = self.command_keys_map[provider_key]()
        logger.debug(f"Initializing provider {provider_key}")

        provider.load_context_from_cli(args)

        required_providers = provider.get_required_providers()
        logger.debug(
            f"Provider {provider_key} requires providers: {required_providers}"
        )

        for required_provider, required_args in required_providers.items():
            required_instance = self._initialize_context_provider(required_provider, args)

        self.history_builder.add_context(provider)
        if provider.counts_as_input():
            self.has_input = True
        return provider

    def refactored_universal_run_chat(self):
        """
        This version of run() method will be universal, regardless if --once is passed, it's using a special command or not,
        it's in interactive mode or not. Each step will be implemented in a separate method and there we'll take care of the details.
        """
        # Initialise
        while True:
            # User round on history
            # LLM round on history
            # Decide to continue or not
            pass
    
    def initialise_chat(self):
        pass
    
    def user_round_on_history(self):
        pass

    def close_if_requested(self):
        pass

    def llm_round_on_history(self):
        pass

    def decide_to_continue(self):
        pass
    
    ################################
    ######## The old code starts here. While not everything here should change, but we should do the quality assessment, revisit everything, 
    ######## only then put them above this line
    ######## While moving, don't remove the original yet, as this logic is used in production. We'll make sure the new logic works, only then deprecate these.

    def run(self):
        logger.debug("Initializing model")
        self.model.initialize()
        logger.debug("Model initialized successfully")

        # Check if input or output is coming from a pipe
        is_input_piped = not sys.stdin.isatty()
        is_output_piped = not sys.stdout.isatty()

        if is_input_piped or is_output_piped:
            logger.debug("Detected non-interactive mode")
            self.handle_non_interactive_input_output(is_input_piped, is_output_piped)
            return

        # Interactive mode
        logger.debug("Starting interactive mode")
        try:
            self.handle_interactive_mode()
        except KeyboardInterrupt:
            logger.info("Chat interrupted by user. Exiting gracefully.")

    def run_once(self):
        logger.debug("Initializing model for single run")
        self.model.initialize()
        logger.debug("Model initialized successfully")

        # Check if input or output is coming from a pipe
        is_input_piped = not sys.stdin.isatty()
        is_output_piped = not sys.stdout.isatty()

        if is_input_piped or is_output_piped:
            logger.debug("Detected non-interactive mode for single run")
            self.handle_non_interactive_input_output(is_input_piped, is_output_piped)
        else:
            logger.debug("Starting single interactive run")
            try:
                self.handle_single_interaction()
            except KeyboardInterrupt:
                logger.info("Chat interrupted by user. Exiting gracefully.")

    def handle_single_interaction(self):
        if self.has_input:
            user_input = ""
            self.has_input = False
        else:
            user_input = self.get_user_input()
            if user_input is None:
                return
        self.send_message_and_print_output(user_input)

    def handle_interactive_mode(self):
        if any(
            isinstance(
                provider,
                (AppendContextProvider, UpdateContextProvider, FillGapsContextProvider),
            )
            and provider.file_path
            for provider in self.history_builder.context_providers
        ):
            self.make_first_request()
            return

        while True:
            if self.has_input:
                user_input = ""
                self.has_input = False
            else:
                user_input = self.get_user_input()
                if user_input is None:
                    return
            self.send_message_and_print_output(user_input)

    def get_user_input(self):
        while True:
            if self.has_input:
                user_input = ""
                self.has_input = False
            else:
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
                        provider.load_context_from_string(args)
                        self.history_builder.add_context(provider)
                        if provider.counts_as_input():
                            self.has_input = True                            
                        self.ui.display_status(f"Context added for /{command}")
                    else:
                        self.ui.display_status(f"Unknown command: /{command}")
                continue

            return user_input

    def make_first_request(self):
        self.history_builder.clear_regular_history()
        if self.has_input:
            message = ""
            self.has_input = False
        else:
            message = self.get_user_input()

        if message is None:
            return False

        self.send_message_and_print_output(message)
        return True

    def handle_non_interactive_input_output(
        self, is_input_piped, is_output_piped
    ):
        message = ""
        if is_input_piped:
            text_context_provider = TextContextProvider()
            text_context_provider.load_context_from_string([sys.stdin.read().strip()])
            self.history_builder.add_context(text_context_provider)
        elif self.has_input:
            message = ""
            self.has_input = False
        else:
            message = self.ui.get_user_input()

        self.send_message_and_print_output(message)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        before_sleep=before_sleep_log(logger, logging.INFO),
    )
    def _send_model_request(self, messages):
        logger.debug("Sending request to model (with retry)")
        response = self.model.send_history(messages)
        logger.debug("Received response from model")
        return response

    def send_message_and_print_output(self, user_input):
        try:
            logger.debug(f"Processing user input: {user_input[:50]}...")
            self.history_builder.add_message("user", user_input)
            messages = self.history_builder.build_messages()
            logger.debug("Sending request to model")
            response = self.ui.display_response(self._send_model_request(messages))
            logger.debug(f"Received response from model: {response[:50]}...")
            self.history_builder.add_message("assistant", response)
            self.apply_special_commands(response)
            return response
        except Exception as e:
            logger.error(f"Error during model request: {str(e)}", exc_info=True)
            self.ui.display_status(f"An error occurred: {str(e)}")
            self.history_builder.pop_message()
        except KeyboardInterrupt:
            logger.info("Chat interrupted by user. Continuing")
            self.history_builder.pop_message()

    def apply_special_commands(self, content: str):
        for provider in self.history_builder.context_providers:
            if isinstance(
                provider,
                (AppendContextProvider, UpdateContextProvider, FillGapsContextProvider),
            ):
                if provider.file_path:
                    if isinstance(provider, AppendContextProvider):
                        file_utils.write_file(
                            provider.file_path, "\n" + content, mode="a"
                        )
                        self.ui.display_status(
                            f"Content appended to {provider.file_path}"
                        )
                    elif isinstance(provider, UpdateContextProvider):
                        file_utils.write_file(provider.file_path, content, mode="w")
                        self.ui.display_status(f"File {provider.file_path} updated")
                    elif isinstance(provider, FillGapsContextProvider):
                        original_content = file_utils.read_file_content(
                            provider.file_path
                        )
                        filled_content = self._fill_gaps(original_content, content)
                        file_utils.write_file(
                            provider.file_path, filled_content, mode="w"
                        )
                        self.ui.display_status(f"Gaps filled in {provider.file_path}")

    def _fill_gaps(self, original_content: str, new_content: str) -> str:
        # Split the original content into lines
        original_lines = original_content.split("\n")

        # Find all gap markers and add indices
        gap_markers = []
        for i, line in enumerate(original_lines):
            if "<GapToFill>" in line:
                gap_markers.append(i)
                original_lines[i] = line.replace(
                    "<GapToFill>", f"<GapToFill index={len(gap_markers)}>"
                )

        # Join the lines with added indices
        indexed_content = "\n".join(original_lines)

        # Send the indexed content to the LLM (this part is handled elsewhere)

        # Extract new content for each gap
        new_content_blocks = re.findall(
            r"<NewGapContent index=(\d+)>(.*?)</NewGapContent>", new_content, re.DOTALL
        )

        # Replace gaps with new content
        for index, content in new_content_blocks:
            index = int(index)
            if index <= len(gap_markers):
                gap_line = gap_markers[index - 1]
                original_lines[gap_line] = (
                    original_lines[gap_line].split("<GapToFill")[0] + content.strip()
                )
        # Join the lines back together
        return "\n".join(original_lines)

    def clear_chat(self):
        self.model.initialize()
        self.history_builder.clear_regular_history()
        self.ui.display_status("Chat history cleared.")
