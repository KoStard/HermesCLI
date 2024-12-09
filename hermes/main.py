import textwrap
from hermes.extensions_loader import load_extensions
from hermes.engine import Engine
from argparse import ArgumentParser, Namespace
from hermes.history import History
from hermes.interface.assistant.model_factory import ModelFactory
from hermes.interface.user.command_completer import CommandCompleter
from hermes.interface.control_panel import LLMControlPanel, UserControlPanel
from hermes.interface.debug.debug_interface import DebugInterface
from hermes.interface.assistant.llm_interface import LLMInterface
from hermes.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.interface.user.markdown_highlighter import MarkdownHighlighter
from hermes.interface.user.stt_input_handler import STTInputHandler
from hermes.interface.user.user_interface import UserInterface
from hermes.participants import DebugParticipant, LLMParticipant, UserParticipant
import configparser
import os

def build_cli_interface(user_control_panel: UserControlPanel, model_factory: ModelFactory):
    parser = ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--model", type=str, help="Model for the LLM", choices=[f"{provider.lower()}/{model_tag}" for provider, model_tag in model_factory.provider_and_model_tag_pairs])
    parser.add_argument("--stt", action="store_true", help="Use Speech to Text mode for input")

    user_control_panel.build_cli_arguments(parser)

    return parser


def main():
    config = load_config()

    notifications_printer = CLINotificationsPrinter()

    user_extra_commands, llm_extra_commands = load_extensions()

    model_factory = ModelFactory(notifications_printer)

    user_control_panel = UserControlPanel(notifications_printer=notifications_printer, extra_commands=user_extra_commands)
    cli_arguments_parser = build_cli_interface(user_control_panel, model_factory)
    cli_args = cli_arguments_parser.parse_args()
    user_input_from_cli = user_control_panel.convert_cli_arguments_to_text(cli_arguments_parser, cli_args)
    stt_input_handler_optional = get_stt_input_handler(cli_args, config)
    user_interface = UserInterface(control_panel=user_control_panel, 
                                   command_completer=CommandCompleter(user_control_panel.get_command_labels()),
                                   markdown_highlighter=MarkdownHighlighter(), 
                                   stt_input_handler=stt_input_handler_optional, 
                                   notifications_printer=notifications_printer,
                                   user_input_from_cli=user_input_from_cli)
    user_participant = UserParticipant(user_interface)

    participants = []
    participants.append(user_participant)

    debug_participant = None
    is_debug_mode = cli_args.debug

    try:
        llm_control_panel = LLMControlPanel(extra_commands=llm_extra_commands)
        model_info_string = cli_args.model
        if not model_info_string:
            model_info_string = get_default_model_info_string(config)
        provider, model_tag = model_info_string.split("/", 1)
        provider = provider.upper()
        config_section = get_config_section(config, provider)
        
        model = model_factory.get_model(provider, model_tag, config_section)

        if is_debug_mode:
            debug_interface = DebugInterface(control_panel=llm_control_panel, model=model)
            debug_participant = DebugParticipant(debug_interface)
            participants.append(debug_participant)

        else:
            llm_interface = LLMInterface(model, control_panel=llm_control_panel)
            llm_participant = LLMParticipant(llm_interface)
            participants.append(llm_participant)
        
        notifications_printer.print_notification(textwrap.dedent(
            f"""
            Welcome to Hermes!
            
            Using model {model_info_string}
            """))

        history = History()
        engine = Engine(participants, history)
        engine.run()
    except KeyboardInterrupt:
        print("\nExiting gracefully...")
    except EOFError:
        print("\nExiting gracefully...")
    except ValueError as e:
        print("Error occured:", e)
    finally:
        # Cleanup debug interface if it exists
        if debug_participant is not None:
            print("Cleaning up debug interface")
            debug_participant.interface.cleanup()


def load_config():
    config = configparser.ConfigParser()
    config.read(os.path.expanduser("~/.config/hermes/config.ini"))
    return config


def get_stt_input_handler(cli_args: Namespace, config: configparser.ConfigParser):
    if cli_args.stt:
        return STTInputHandler(api_key=config["GROQ"]["api_key"])
    else:
        return None

def get_default_model_info_string(config: configparser.ConfigParser):
    return config["BASE"]["model"]

def get_config_section(config: configparser.ConfigParser, provider: str):
    if provider not in config.sections():
        raise ValueError(f"Config section {provider} is not found. Please double check it and specify it in the config file ~/.config/hermes/config.ini.")
    return config[provider]


if __name__ == "__main__":
    main()
