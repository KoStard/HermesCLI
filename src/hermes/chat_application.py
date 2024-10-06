import argparse
import logging
import shlex
import sys
from typing import Dict, List, Type

from tenacity import (before_sleep_log, retry, stop_after_attempt,
                      wait_exponential)

from hermes.chat_models.base import ChatModel
from hermes.chat_ui import ChatUI
from hermes.context_providers.base import ContextProvider
from hermes.history_builder import HistoryBuilder

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

        # Loading history before instantiating the context providers
        if args.load_history:
            self._load_history_from_file(args.load_history)

        self._setup_initial_context_providers(args)
        self._user_commands_queue = []

        logger.debug("ChatApplication initialization complete")

    def _setup_initial_context_providers(self, args: argparse.Namespace):
        for key, value in vars(args).items():
            if key in self.command_keys_map and value:
                self._setup_initial_context_provider(key, args, None, permanent=True)

    def _setup_initial_context_provider(
        self,
        provider_key: str,
        cli_args: argparse.Namespace | None,
        regular_args: List[str] | None,
        permanent: bool
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
            self._setup_initial_context_provider(required_provider, None, required_args, permanent=permanent)

        self.history_builder.add_context(provider, provider.counts_as_input(), permanent=permanent)
        return provider

    def run_chat(self, run_once=False):
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
        keyboard_interrupt = False
        while self.history_builder.requires_user_input():
            try:
                if self.get_user_input() == 'exit':
                    return 'exit'
            except KeyboardInterrupt:
                if not keyboard_interrupt:
                    logger.info("\nChat interrupted by user. Continuing")
                    keyboard_interrupt = True
                else:
                    return 'exit'

    def llm_round(self):
        self._llm_interact()
        self._llm_act()
    
    def _llm_interact(self):
        messages = self.history_builder.build_messages()
        try:
            logger.debug("Sending request to model")
            response = self.ui.display_response(self._send_model_request(messages))
            logger.debug(f"Received response from model: {response[:50]}...")
            self.history_builder.add_assistant_reply(response)
        except Exception as e:
            logger.error(f"Error during model request: {str(e)}", exc_info=True)
            self.ui.display_status(f"An error occurred: {str(e)}")
            raise e
        except KeyboardInterrupt:
            logger.info("Chat interrupted by user. Continuing")
            self.history_builder.add_assistant_reply("<RESPONSE_FAILED_TO_COMMUNICATE>")
        
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
        extra_commands = {
            "/exit",
            "/quit",
            "/q",
            "/clear",
            "/save_history",
            "/load_history"
        }   

        if not self._user_commands_queue:
            user_input = self.ui.get_user_input()

            words = shlex.split(user_input)
            full_commands = self._split_list(words, lambda x: x.startswith("/") and (x[1:] in self.command_keys_map or x in extra_commands))
            for command_and_args in full_commands:
                self._user_commands_queue.append(command_and_args)

        command_and_args = self._user_commands_queue.pop(0)
        command = command_and_args[0]
        command = command.lower()
        args = command_and_args[1:]

        if command in ["/exit", "/quit", "/q"]:
            return 'exit'
        elif command == "/clear":
            self.clear_chat()
        elif command == "/save_history":
            self._save_history(args)
        elif command == "/load_history":
            self._load_history(args)
        elif command.startswith("/"):
            self._run_command(command[1:], args)
        else:
            used_input_instance = " ".join(command_and_args)
            self.history_builder.add_user_input(used_input_instance, active=True)
    
    def _run_command(self, command, args):
        self._setup_initial_context_provider(command, None, args, permanent=False)
        self.ui.display_status(f"Context added for /{command}")
            
    def _split_list(self, lst, checker):
        result = []
        current_sublist = []

        for item in lst:
            if checker(item):
                if current_sublist:
                    result.append(current_sublist)
                current_sublist = [item]
            else:
                current_sublist.append(item)

        if current_sublist:
            result.append(current_sublist)

        return result

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

    def _save_history(self, args):
        if not args:
            file_path = 'hermes_history.json'
        else:
            file_path = ' '.join(args)
        try:
            self.history_builder.save_history(file_path)
            self.ui.display_status(f"Chat history saved to {file_path}")
        except Exception as e:
            self.ui.display_status(f"Error saving chat history: {str(e)}")

    def _load_history(self, args):
        if not args:
            self.ui.display_status("Please provide a file path to load the history from.")
            return
        file_path = ' '.join(args)
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
