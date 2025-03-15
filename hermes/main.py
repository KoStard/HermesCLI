import textwrap
from hermes.extensions_loader import load_extensions
from hermes.engine import Engine
from argparse import ArgumentParser, Namespace
from hermes.history import History
from hermes.interface.assistant.chat_assistant.control_panel import ChatAssistantControlPanel
from hermes.interface.assistant.deep_research_assistant.interface import DeepResearchAssistantInterface
from hermes.interface.assistant.model_factory import ModelFactory
from hermes.interface.user.command_completer import CommandCompleter
from hermes.interface.control_panel import CommandsLister
from hermes.interface.debug.debug_interface import DebugInterface
from hermes.interface.assistant.chat_assistant.interface import ChatAssistantInterface
from hermes.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.interface.user.markdown_highlighter import MarkdownHighlighter
from hermes.interface.user.stt_input_handler import STTInputHandler
from hermes.interface.user.user_control_panel import UserControlPanel
from hermes.interface.user.user_interface import UserInterface
from hermes.exa_client import ExaClient
from hermes.participants import DebugParticipant, LLMParticipant, UserParticipant
import configparser
import os


def build_cli_interface(
    user_control_panel: UserControlPanel, model_factory: ModelFactory
):
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="execution_mode", required=True)
    chat_parser = subparsers.add_parser("chat", help="Get command information")

    chat_parser.add_argument("--debug", action="store_true")
    chat_parser.add_argument(
        "--model",
        type=str,
        help=f"Model for the LLM (suggested models: {', '.join(f'{provider.lower()}/{model_tag}' for provider, model_tag in model_factory.get_provider_model_pairs())})",
    )
    chat_parser.add_argument(
        "--deep-research",
        metavar="PATH",
        help="Use the Deep Research Assistant interface with path to research folder",
        type=str,
    )
    chat_parser.add_argument(
        "--stt", action="store_true", help="Use Speech to Text mode for input"
    )
    chat_parser.add_argument(
        "--no-markdown",
        action="store_true",
        help="Disable markdown highlighting for output",
    )

    # Utils command
    utils_parser = subparsers.add_parser("utils", help="Utility commands")
    utils_subparsers = utils_parser.add_subparsers(dest="utils_command", required=True)

    # Extract PDF pages command
    extract_pdf_parser = utils_subparsers.add_parser(
        "extract_pdf_pages",
        help="Extract pages from a PDF file. Will be saved as original_path/original_name_extracted.pdf",
    )
    extract_pdf_parser.add_argument("filepath", type=str, help="Path to the PDF file")
    extract_pdf_parser.add_argument(
        "pages", type=str, help="Pages to extract (e.g. {1,4:5})"
    )

    # Get URL content command
    get_url_parser = utils_subparsers.add_parser(
        "get_url", help="Get raw content from a URL using standard HTTP"
    )
    get_url_parser.add_argument("url", type=str, help="URL to fetch content from")
    get_url_parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: url_hostname.txt)",
        default=None,
    )

    # Get URL content via Exa command
    get_url_exa_parser = utils_subparsers.add_parser(
        "get_url_exa", help="Get enhanced content from a URL using Exa API"
    )
    get_url_exa_parser.add_argument("url", type=str, help="URL to fetch content from")
    get_url_exa_parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: url_hostname.txt)",
        default=None,
    )

    # Exa search command
    exa_search_parser = utils_subparsers.add_parser(
        "exa_search", help="Search the web using Exa API"
    )
    exa_search_parser.add_argument("query", type=str, help="Search query")
    exa_search_parser.add_argument(
        "--num_results",
        type=int,
        help="Number of results to return (default: 5)",
        default=5,
    )

    # Info command
    info_parser = subparsers.add_parser("info", help="Get command information")
    info_subparsers = info_parser.add_subparsers(dest="info_command", required=True)

    # List assistant commands
    info_subparsers.add_parser(
        "list-assistant-commands", help="List all assistant commands"
    )

    # List user commands
    info_subparsers.add_parser("list-user-commands", help="List all user commands")

    user_control_panel.build_cli_arguments(chat_parser)

    return parser, utils_subparsers


def main():
    config = load_config()

    # Read command status overrides from config
    command_status_overrides = {}
    if "BASE" in config and "llm_command_status_overrides" in config["BASE"]:
        try:
            # Parse the overrides string into a dict
            raw_overrides = config["BASE"]["llm_command_status_overrides"].strip()
            if raw_overrides:
                # Format should be: command_id:status,command_id2:status2
                for override in raw_overrides.split(","):
                    command_id, status = override.split(":")
                    command_status_overrides[command_id.strip()] = (
                        status.strip().upper()
                    )
        except Exception as e:
            print(
                f"Warning: Failed to parse llm_command_status_overrides from config: {e}"
            )

    notifications_printer = CLINotificationsPrinter()

    user_extra_commands, llm_extra_commands, extension_utils_builders = (
        load_extensions()
    )

    model_factory = ModelFactory(notifications_printer)

    # Initialize Exa client if configured
    exa_client = None
    if "EXA" in config and "api_key" in config["EXA"]:
        exa_client = ExaClient(config["EXA"]["api_key"])

    llm_control_panel = ChatAssistantControlPanel(
        notifications_printer=notifications_printer,
        extra_commands=llm_extra_commands,
        exa_client=exa_client,
        command_status_overrides=command_status_overrides,
    )
    user_control_panel = UserControlPanel(
        notifications_printer=notifications_printer,
        extra_commands=user_extra_commands,
        exa_client=exa_client,
        llm_control_panel=llm_control_panel,
    )

    cli_arguments_parser, utils_subparsers = build_cli_interface(
        user_control_panel, model_factory
    )

    extension_utils_visitors = []

    # Register extension utils
    for extension_utils_builder in extension_utils_builders:
        extension_utils_visitors.append(extension_utils_builder(utils_subparsers))

    cli_args = cli_arguments_parser.parse_args()

    if cli_args.execution_mode == "info":
        execute_info_command(
            cli_args,
            user_control_panel.get_commands(),
            llm_control_panel.get_commands(),
        )
        return
    elif cli_args.execution_mode == "utils":
        execute_utils_command(cli_args, config, extension_utils_visitors)
        return
    user_input_from_cli = user_control_panel.convert_cli_arguments_to_text(
        cli_arguments_parser, cli_args
    )
    stt_input_handler_optional = get_stt_input_handler(cli_args, config)
    markdown_highlighter = None if cli_args.no_markdown else MarkdownHighlighter()
    user_interface = UserInterface(
        control_panel=user_control_panel,
        command_completer=CommandCompleter(user_control_panel.get_command_labels()),
        markdown_highlighter=markdown_highlighter,
        stt_input_handler=stt_input_handler_optional,
        notifications_printer=notifications_printer,
        user_input_from_cli=user_input_from_cli,
    )
    user_participant = UserParticipant(user_interface)

    debug_participant = None
    is_debug_mode = cli_args.debug

    try:
        model_info_string = cli_args.model
        if not model_info_string:
            model_info_string = get_default_model_info_string(config)
        if not model_info_string:
            raise ValueError(
                "No model specified. Please specify a model using the --model argument or add a default model in the config file ~/.config/hermes/config.ini."
            )
        if "/" not in model_info_string:
            raise ValueError(
                "Model info string should be in the format provider/model_tag"
            )
        provider, model_tag = model_info_string.split("/", 1)
        provider = provider.upper()
        config_section = get_config_section(config, provider)

        model = model_factory.get_model(provider, model_tag, config_section)

        if is_debug_mode:
            debug_interface = DebugInterface(
                control_panel=llm_control_panel, model=model
            )
            debug_participant = DebugParticipant(debug_interface)
            assistant_participant = debug_participant
        elif cli_args.deep_research:
            # Use the Deep Research Assistant interface with the specified path
            research_path = os.path.abspath(cli_args.deep_research)
            deep_research_interface = DeepResearchAssistantInterface(
                model=model,
                research_path=research_path
            )
            deep_research_participant = LLMParticipant(deep_research_interface)
            assistant_participant = deep_research_participant
            
            notifications_printer.print_notification(
                f"Using Deep Research Assistant interface with research directory: {research_path}"
            )
        else:
            llm_interface = ChatAssistantInterface(model, control_panel=llm_control_panel)
            llm_participant = LLMParticipant(llm_interface)
            assistant_participant = llm_participant

        notifications_printer.print_notification(
            textwrap.dedent(
                f"""
            Welcome to Hermes!
            
            Using model {model_info_string}
            """
            )
        )

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


def execute_utils_command(cli_args, config, extension_utils_visitors):
    if cli_args.utils_command == "extract_pdf_pages":
        pages = []
        pages_str = cli_args.pages.strip("{}")
        for part in pages_str.split(","):
            if ":" in part:
                start, end = map(int, part.split(":"))
                pages.extend(range(start, end + 1))
            else:
                pages.append(int(part))

        from PyPDF2 import PdfReader, PdfWriter
        import os

        reader = PdfReader(cli_args.filepath)
        writer = PdfWriter()

        for page_num in pages:
            if 1 <= page_num <= len(reader.pages):
                writer.add_page(reader.pages[page_num - 1])

        output_path = f"{os.path.splitext(cli_args.filepath)[0]}_extracted.pdf"
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        print(f"Extracted pages saved to: {output_path}")
    elif cli_args.utils_command == "get_url":
        from markitdown import MarkItDown
        import requests

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }
        response = requests.get(cli_args.url, headers=headers)
        response.raise_for_status()
        markitdown = MarkItDown()
        conversion_result = markitdown.convert(response)
        markdown_content = conversion_result.text_content
        print(f"\n# URL Content: {cli_args.url}\n")
        print(markdown_content)
    elif cli_args.utils_command == "get_url_exa":
        client = ExaClient(
            config["EXA"]["api_key"]
        )  # Will fail naturally if config is missing
        result = client.get_contents(cli_args.url)

        if not result:
            raise ValueError(f"No content found for URL: {cli_args.url}")

        print(f"\n# Exa AI Summary: {cli_args.url}\n")
        print(result[0].title)
        print(result[0].text)
        print("Last updated:", result[0].published_date)
    elif cli_args.utils_command == "exa_search":
        client = ExaClient(
            config["EXA"]["api_key"]
        )  # Will fail naturally if config is missing
        results = client.search(cli_args.query, cli_args.num_results)

        if not results:
            print("No results found")
            return

        print(f"\n# Exa Search Results for: {cli_args.query}\n")
        for i, result in enumerate(results, 1):
            print(f"Result {i}:")
            print(f"  Title: {result.title}")
            print(f"  URL: {result.url}")
            if result.author:
                print(f"  Author: {result.author}")
            if result.published_date:
                print(f"  Published: {result.published_date}")
            print()
    else:
        for extension_util_visitor in extension_utils_visitors:
            extension_util_visitor(cli_args, config)


def load_config():
    config_path = os.path.expanduser("~/.config/hermes/config.ini")
    if not os.path.exists(config_path):
        raise ValueError(
            "Configuration file at ~/.config/hermes/config.ini not found. Please go to https://github.com/KoStard/HermesCLI/ and follow the setup steps."
        )

    config = configparser.ConfigParser()
    config.read(config_path)
    return config


def get_stt_input_handler(cli_args: Namespace, config: configparser.ConfigParser):
    if cli_args.stt:
        if "GROQ" not in config or "api_key" not in config["GROQ"]:
            raise ValueError(
                "Please set the GROQ api key in ~/.config/hermes/config.ini"
            )
        return STTInputHandler(api_key=config["GROQ"]["api_key"])
    else:
        return None


def get_default_model_info_string(config: configparser.ConfigParser):
    if "BASE" not in config:
        return None
    base_section = config["BASE"]
    return base_section.get("model")


def get_config_section(config: configparser.ConfigParser, provider: str):
    if provider not in config.sections():
        raise ValueError(
            f"Config section {provider} is not found. Please double check it and specify it in the config file ~/.config/hermes/config.ini. You might need to specify the api_key there."
        )
    return config[provider]


if __name__ == "__main__":
    main()
