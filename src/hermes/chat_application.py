import argparse
from typing import List, Type
import sys
import re
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log

from hermes.chat_models.base import ChatModel
from hermes.file_processors.base import FileProcessor
from hermes.prompt_builders.base import PromptBuilder
from hermes.chat_ui import ChatUI
from hermes.history_builder import HistoryBuilder
from hermes.context_providers.base import ContextProvider

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
        self.request_failed = False

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

        logger.debug("ChatApplication initialization complete")

    def _initialize_context_providers(self, args: argparse.Namespace):
        for key, value in vars(args).items():
            if key in self.command_keys_map and value is not None:
                self._initialize_context_provider(key, args, None)

    def _initialize_context_provider(
        self,
        provider_key: str,
        cli_args: argparse.Namespace | None,
        regular_args: List[str] | None,
    ):
        provider = self.command_keys_map[provider_key]()
        logger.debug(f"Initializing provider {provider_key}")

        if cli_args is not None:
            provider.load_context_from_cli(cli_args)
        else:
            provider.load_context_from_string(regular_args)

        required_providers = provider.get_required_providers()
        logger.debug(
            f"Provider {provider_key} requires providers: {required_providers}"
        )

        for required_provider, required_args in required_providers.items():
            self._initialize_context_provider(required_provider, None, required_args)

        self.history_builder.add_context(provider, provider.counts_as_input())
        return provider

    def refactored_universal_run_chat(self, run_once=False):
        """
        This version of run() method will be universal, regardless if --once is passed, it's using a special command or not,
        it's in interactive mode or not. Each step will be implemented in a separate method and there we'll take care of the details.
        """
        self.initialise_chat()
        
        while True:
            if self.user_round() == 'exit':
                break
            
            self.llm_round()
            
            if not self.decide_to_continue(run_once):
                break
    
    def initialise_chat(self):
        logger.debug("Initializing model")
        self.model.initialize()
        logger.debug("Model initialized successfully")
    
    def user_round(self):
        while self.history_builder.requires_user_input() or self.request_failed:
            if self.get_user_input() == 'exit':
                return 'exit'

    def llm_round(self):
        self._llm_interact()
        self._llm_act()
    
    def _llm_interact(self):
        self.request_failed = False
        messages = self.history_builder.build_messages()
        try:
            logger.debug("Sending request to model")
            response = self.ui.display_response(self._send_model_request(messages))
            logger.debug(f"Received response from model: {response[:50]}...")
            self.history_builder.add_assistant_reply(response)
        except Exception as e:
            logger.error(f"Error during model request: {str(e)}", exc_info=True)
            self.ui.display_status(f"An error occurred: {str(e)}")
            self.request_failed = True
            raise e
        except KeyboardInterrupt:
            logger.info("Chat interrupted by user. Continuing")
            self.request_failed = True
        
    def _llm_act(self):
        recent_llm_response = self.history_builder.get_recent_llm_response()
        # We sent these context providers that have actions to the LLM, received response, now we'll need to act on them
        self.history_builder.run_pending_actions(
            lambda action: action.perform_action(recent_llm_response),
            self.ui
        )
    
    def decide_to_continue(self, run_once):
        is_input_piped = not sys.stdin.isatty()
        is_output_piped = not sys.stdout.isatty()
        return not run_once and not is_input_piped and not is_output_piped
    
    def get_user_input(self):
        while True:
            user_input = self.ui.get_user_input()
            user_input_lower = user_input.lower()

            if user_input_lower in ["exit", "quit", "q"]:
                return 'exit'
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
                        self.history_builder.add_context(provider, provider.counts_as_input())
                        self.ui.display_status(f"Context added for /{command}")
                    else:
                        self.ui.display_status(f"Unknown command: /{command}")
                return
            else:
                self.history_builder.add_user_input(user_input, active=True)
                return

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        before_sleep=before_sleep_log(logger, logging.INFO),
    )
    def _send_model_request(self, messages):
        logger.debug("Sending request to model (with retry)")
        logger.debug("Messages to send:")
        for message in messages:
            logger.debug(message)
        response = self.model.send_history(messages)
        logger.debug("Received response from model")
        return response

    def clear_chat(self):
        self.model.initialize()
        self.history_builder.clear_regular_history()
        self.ui.display_status("Chat history cleared.")
