import argparse
import logging
import shlex
import sys
import os
from datetime import datetime
from typing import Callable, Dict, List, Tuple, Type, Generator

from tenacity import (before_sleep_log, retry, stop_after_attempt,
                      wait_exponential, retry_if_exception_type, retry_if_result)

from hermes.chat_models.base import ChatModel
from hermes.chat_ui import ChatUI
from hermes.context_providers.base import ContextProvider
from hermes.history_builder import HistoryBuilder
from hermes.utils.commands_extractor import extract_commands

# Set up logging
logger = logging.getLogger(__name__)


class ChatApplication:
    def __init__(
        self,
        model: ChatModel,
        ui: ChatUI,
        history_builder: HistoryBuilder,
        command_keys_map: Dict[str, Type[ContextProvider]],
        args: argparse.Namespace,
    ):
        self.model = model
        self.ui = ui
        self.history_builder = history_builder
        self.command_keys_map = command_keys_map
        self.is_model_initialised = False

        # Loading history before instantiating the context providers
        if args.load_history:
            self._load_history_from_file(args.load_history)

        self._setup_initial_context_providers(args)
        self._user_commands_queue: List[Tuple[str, str]] = []

        self.extra_commands = {
            "/exit",
            "/quit",
            "/q",
            "/clear",
            "/save_history",
            "/load_history"
        }

        logger.debug("ChatApplication initialization complete")

    def _setup_initial_context_providers(self, args: argparse.Namespace):
        for key, value in vars(args).items():
            # The value is checked here, as the keys are always present in the namespace, but their values are None
            if key in self.command_keys_map and value:
                try:
                    provider_instances = self._setup_initial_context_provider(key, args, None, permanent=True)
                    for provider in provider_instances:
                        self.history_builder.add_context(provider, provider.counts_as_input(), permanent=True)
                except Exception as e:
                    logger.error(f"Error during setup of initial context providers with {key}: {str(e)}", exc_info=True)

    def _setup_initial_context_provider(
        self,
        provider_key: str,
        cli_args: argparse.Namespace | None,
        regular_args: List[str] | None,
        permanent: bool
    ) -> List[ContextProvider]:
        provider = self.command_keys_map[provider_key]()
        logger.debug(f"Initializing provider {provider_key}")

        provider.load_context(cli_args, regular_args)

        required_providers = provider.get_required_providers()
        logger.debug(
            f"Provider {provider_key} requires providers: {required_providers}"
        )

        provider_instances = []

        for required_provider, required_args in required_providers.items():
            provider_instances.extend(self._setup_initial_context_provider(required_provider, None, required_args, permanent=permanent))

        provider_instances.append(provider)

        return provider_instances

    def run_chat(self, run_once=False):
        """
        This version of run() method will be universal, regardless if --once is passed, it's using a special command or not,
        it's in interactive mode or not. Each step will be implemented in a separate method and there we'll take care of the details.
        """

        try:
            while True:
                if self.user_round() == 'exit':
                    break
                
                self.llm_round()
                
                if not self.decide_to_continue(run_once):
                    break
        except (KeyboardInterrupt, EOFError):
            return
        except Exception as e:
            file_path = self._save_history(None)
            logger.error(f"Chat history saved to {file_path} before exiting")
            raise e
        
    def user_round(self):
        keyboard_interrupt = False
        while self.history_builder.requires_user_input():
            try:
                if self.get_user_input() == 'exit':
                    return 'exit'
            except (KeyboardInterrupt, EOFError):
                if not keyboard_interrupt:
                    logger.info("\nChat interrupted by user. Continuing")
                    keyboard_interrupt = True
                else:
                    return 'exit'
            except Exception as e:
                logger.error(f"Error during user round: {str(e)}", exc_info=True)
                self.history_builder.force_need_for_user_input()

    def llm_round(self):
        self._llm_interact()
        self._llm_act()
    
    def _llm_interact(self):
        messages = self.history_builder.build_messages()
        try:
            logger.debug("Sending request to model")
            response = self._send_model_request(messages)
            if response is None:
                retry = self.ui.get_user_input("Model request failed. Retry? (Y/n): ").lower()
                if retry in ['y', 'yes', '']:
                    logger.info("User chose to retry the model request")
                    return self._llm_interact()
                else:
                    logger.debug("User chose not to retry the model request")
                    self.ui.display_status("Model request cancelled by user.")
                    self.history_builder.force_need_for_user_input()
                    return

            response = self.ui.display_response(response)
            logger.debug(f"Received response from model: {response[:50]}...")
            self.history_builder.add_assistant_reply(response)
        except KeyboardInterrupt:
            logger.info("Chat interrupted by user. Continuing")
            self.history_builder.force_need_for_user_input()
        
    def _llm_act(self):
        recent_llm_response = self.history_builder.get_recent_llm_response()
        # We sent these context providers that have actions to the LLM, received response, now we'll need to act on them
        self.history_builder.run_pending_actions(
            lambda action: action.perform_action(recent_llm_response),
            self.ui
        )
    
    def decide_to_continue(self, run_once):
        is_output_piped = not sys.stdout.isatty()
        return not run_once and not is_output_piped
    
    def get_user_input(self):
        if not self._user_commands_queue:
            user_input = self.ui.get_user_input()

            full_commands = self._process_user_input(user_input)
            for command, args in full_commands:
                self._user_commands_queue.append((command, args))

        command, args = self._user_commands_queue.pop(0)
        lower_command = command.lower()

        if lower_command in ["/exit", "/quit", "/q"]:
            return 'exit'
        elif lower_command == "/clear":
            self.clear_chat()
        elif lower_command == "/save_history":
            self._save_history(args)
        elif lower_command == "/load_history":
            self._load_history(args)
        elif lower_command.startswith("/"):
            self._run_command(lower_command[1:], args)
        else:
            self.history_builder.add_user_input(args, active=True)
    
    def _run_command(self, command: str, args: str):
        shlexer = shlex.shlex(args, posix=True)
        shlexer.quotes = '"'
        shlexer.commenters = ''
        shlexer.whitespace_split = True
        shlex_args = list(shlexer)

        provider_instances = self._setup_initial_context_provider(command, None, shlex_args, permanent=False)
        for provider in provider_instances:
            self.history_builder.add_context(provider, provider.counts_as_input(), permanent=False)
        if command != 'prompt':
            self.ui.display_status(f"Context added for /{command}")
            
    def _process_user_input(self, user_input: str) -> List[Tuple[str, str]]:
        commands_set = set(self.command_keys_map.keys()) | {e[1:] for e in self.extra_commands}

        return extract_commands(user_input, commands_set)


    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=6),
        before_sleep=before_sleep_log(logger, logging.INFO),
        retry=(
            retry_if_exception_type(Exception) |
            retry_if_result(lambda result: result is None)
        )
    )
    def _send_model_request(self, messages) -> Generator[str, None, None] | None:
        logger.debug("Sending request to model (with retry)")
        logger.debug("Messages to send:")
        for message in messages:
            logger.debug(message)
        try:
            if not self.is_model_initialised:
                self._initialise_model()
                self.is_model_initialised = True
            
            response_generator = self.model.send_history(messages)
            
            # Try to get the first chunk to ensure the generator is working
            try:
                first_chunk = next(response_generator)
                logger.debug("Received first chunk of response from model")
                
                # Create a new generator that yields the first chunk and then the rest
                def safe_generator():
                    yield first_chunk
                    yield from response_generator
                
                return safe_generator()
            except StopIteration:
                logger.error("Model returned an empty response")
                return None
            
        except Exception as e:
            logger.error(f"Error during model request: {str(e)}", exc_info=True)
            return None
    
    def _initialise_model(self):
        logger.debug("Initializing model")
        self.model.initialize()
        logger.debug("Model initialized successfully")

    def clear_chat(self):
        self.history_builder.clear_regular_history()
        self.ui.display_status("Chat history cleared.")

    def _save_history(self, filename: str | None):
        if not filename:
            # Create a timestamp string for the default filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hermes_history_{timestamp}.json"
        else:
            # Ensure the filename ends with .json
            if not filename.lower().endswith('.json'):
                filename += '.json'

        try:
            self.history_builder.save_history(filename)
            readable_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.ui.display_status(f"Chat history saved to '{filename}' at {readable_time}")
        except Exception as e:
            self.ui.display_status(f"Error saving chat history: {str(e)}")
        
        return filename

    def _load_history(self, file_path: str | None):
        if not file_path:
            self.ui.display_status("Please provide a file path to load the history from.")
            return
        try:
            self.history_builder.load_history(file_path)
            self.ui.display_status(f"Chat history loaded from {file_path}")
        except Exception as e:
            self.ui.display_status(f"Error loading chat history: {str(e)}")

    def _load_history_from_file(self, file_path: str):
        try:
            self.history_builder.load_history(file_path)
            self.ui.display_status(f"Chat history loaded from {file_path}")
        except Exception as e:
            self.ui.display_status(f"Error loading chat history: {str(e)}")
            logger.error(f"Error loading chat history from {file_path}: {str(e)}", exc_info=True)
