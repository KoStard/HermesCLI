import textwrap
from hermes.extensions_loader import load_extensions
from hermes.engine import Engine
from argparse import ArgumentParser, Namespace
from hermes.history import History
from hermes.interface.assistant.llm_control_panel import LLMControlPanel
from hermes.interface.assistant.model_factory import ModelFactory
from hermes.interface.user.command_completer import CommandCompleter
from hermes.interface.control_panel import CommandsLister
from hermes.interface.debug.debug_interface import DebugInterface
from hermes.interface.assistant.llm_interface import LLMInterface
from hermes.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.interface.user.markdown_highlighter import MarkdownHighlighter
from hermes.interface.user.stt_input_handler import STTInputHandler
from hermes.interface.user.user_control_panel import UserControlPanel
from hermes.interface.user.user_interface import UserInterface
from hermes.participants import DebugParticipant, LLMParticipant, UserParticipant
import configparser
import os

def build_cli_interface(user_control_panel: UserControlPanel, model_factory: ModelFactory):
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="execution_mode", required=True)
    chat_parser = subparsers.add_parser("chat", help="Get command information")

    chat_parser.add_argument("--debug", action="store_true")
    chat_parser.add_argument("--model", type=str, help=f"Model for the LLM (suggested models: {', '.join(f'{provider.lower()}/{model_tag}' for provider, model_tag in model_factory.get_provider_model_pairs())})")
    chat_parser.add_argument("--stt", action="store_true", help="Use Speech to Text mode for input")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Get command information")
    info_subparsers = info_parser.add_subparsers(dest="info_command", required=True)
    
    # List assistant commands
    info_subparsers.add_parser(
        "list-assistant-commands",
        help="List all assistant commands"
    )
    
    # List user commands
    info_subparsers.add_parser(
        "list-user-commands",
        help="List all user commands"
    )

    user_control_panel.build_cli_arguments(chat_parser)

    return parser


def main():
    config = load_config()

    notifications_printer = CLINotificationsPrinter()

    user_extra_commands, llm_extra_commands = load_extensions()

    model_factory = ModelFactory(notifications_printer)

    user_control_panel = UserControlPanel(notifications_printer=notifications_printer, extra_commands=user_extra_commands)
    llm_control_panel = LLMControlPanel(notifications_printer=notifications_printer, extra_commands=llm_extra_commands)
    cli_arguments_parser = build_cli_interface(user_control_panel, model_factory)
    cli_args = cli_arguments_parser.parse_args()
    
    if cli_args.execution_mode == "info":
        execute_info_command(cli_args, user_control_panel.get_commands(), llm_control_panel.get_commands())
        return
    user_input_from_cli = user_control_panel.convert_cli_arguments_to_text(cli_arguments_parser, cli_args)
    stt_input_handler_optional = get_stt_input_handler(cli_args, config)
    user_interface = UserInterface(control_panel=user_control_panel, 
                                   command_completer=CommandCompleter(user_control_panel.get_command_labels()),
                                   markdown_highlighter=MarkdownHighlighter(), 
                                   stt_input_handler=stt_input_handler_optional, 
                                   notifications_printer=notifications_printer,
                                   user_input_from_cli=user_input_from_cli)
    user_participant = UserParticipant(user_interface)

    debug_participant = None
    is_debug_mode = cli_args.debug

    try:
        model_info_string = cli_args.model
        if not model_info_string:
            model_info_string = get_default_model_info_string(config)
        if not model_info_string:
            raise ValueError("No model specified. Please specify a model using the --model argument or add a default model in the config file ~/.config/hermes/config.ini.")
        if "/" not in model_info_string:
            raise ValueError("Model info string should be in the format provider/model_tag")
        provider, model_tag = model_info_string.split("/", 1)
        provider = provider.upper()
        config_section = get_config_section(config, provider)
        
        model = model_factory.get_model(provider, model_tag, config_section)

        if is_debug_mode:
            debug_interface = DebugInterface(control_panel=llm_control_panel, model=model)
            debug_participant = DebugParticipant(debug_interface)
            assistant_participant = debug_participant

        else:
            llm_interface = LLMInterface(model, control_panel=llm_control_panel)
            llm_participant = LLMParticipant(llm_interface)
            assistant_participant = llm_participant
        
        notifications_printer.print_notification(textwrap.dedent(
            f"""
            Welcome to Hermes!
            
            Using model {model_info_string}
            """))

        history = History()
        engine = Engine(user_participant, assistant_participant, history)
        engine.run()
    except KeyboardInterrupt:
        print("\nExiting gracefully...")
    except EOFError:
        print("\nExiting gracefully...")
    except ValueError as e:
        print("Error occured:")
        raise e
    finally:
        # Cleanup debug interface if it exists
        if debug_participant is not None:
            print("Cleaning up debug interface")
            debug_participant.interface.cleanup()


def execute_info_command(cli_args, user_commands, llm_commands):
    lister = CommandsLister()
    if cli_args.info_command == "list-assistant-commands":
        lister.print_commands(llm_commands)
    elif cli_args.info_command == "list-user-commands":
        lister.print_commands(user_commands)


def load_config():
    config_path = os.path.expanduser("~/.config/hermes/config.ini")
    if not os.path.exists(config_path):
        raise ValueError("Configuration file at ~/.config/hermes/config.ini not found. Please go to https://github.com/KoStard/HermesCLI/ and follow the setup steps.")

    config = configparser.ConfigParser()
    config.read(config_path)
    return config


def get_stt_input_handler(cli_args: Namespace, config: configparser.ConfigParser):
    if cli_args.stt:
        if 'GROQ' not in config or 'api_key' not in config['GROQ']:
            raise ValueError("Please set the GROQ api key in ~/.config/hermes/config.ini")
        return STTInputHandler(api_key=config["GROQ"]["api_key"])
    else:
        return None

def get_default_model_info_string(config: configparser.ConfigParser):
    if 'BASE' not in config:
        return None
    base_section = config['BASE']
    return base_section.get('model')

def get_config_section(config: configparser.ConfigParser, provider: str):
    if provider not in config.sections():
        raise ValueError(f"Config section {provider} is not found. Please double check it and specify it in the config file ~/.config/hermes/config.ini. You might need to specify the api_key there.")
    return config[provider]


if __name__ == "__main__":
    main()
