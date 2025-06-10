from argparse import ArgumentParser, Namespace
from enum import Enum, auto

from hermes.chat.interface.user.control_panel.user_control_panel import UserControlPanel


class ExecutionMode(Enum):
    CHAT = auto()
    SIMPLE_AGENT = auto()
    RESEARCH = auto()
    UTILS = auto()

    @staticmethod
    def get_from_cli_args(cli_args: Namespace) -> "ExecutionMode":
        execution_mode_str = cli_args.execution_mode
        if execution_mode_str == "chat":
            return ExecutionMode.CHAT
        if execution_mode_str == "simple-agent":
            return ExecutionMode.SIMPLE_AGENT
        if execution_mode_str == "research":
            return ExecutionMode.RESEARCH
        if execution_mode_str == "utils":
            return ExecutionMode.UTILS
        raise ValueError("Unknown Execution Mode " + execution_mode_str)


class CLIParser:
    def __init__(self, provider_model_pairs: list[tuple]):
        self._provider_model_pairs = provider_model_pairs

        self._parser = ArgumentParser()
        subparsers = self._parser.add_subparsers(dest="execution_mode", required=True)

        self._chat_parser = self._build_chat_parser(subparsers)
        self._simple_agent_parser = self._build_simple_agent_parser(subparsers)
        self._research_parser = self._build_research_parser(subparsers)
        self._utils_subparsers = self._build_utils_parser(subparsers)
        self._build_info_parser(subparsers)

    def add_user_control_panel_arguments(self, user_control_panel: UserControlPanel):
        user_control_panel.build_cli_arguments_for_chat(self._chat_parser)
        user_control_panel.build_cli_arguments_for_simple_agent(self._simple_agent_parser)
        user_control_panel.build_cli_arguments_for_research(self._research_parser)

    def register_utility_extensions_and_get_executor_visitors(self, extension_utils_builders: list) -> list:
        extension_visitors = []
        for builder in extension_utils_builders:
            extension_visitors.append(builder(self._utils_subparsers))
        return extension_visitors

    def parse_args(self):
        return self._parser.parse_args()

    def _build_chat_parser(self, subparsers):
        chat_parser = subparsers.add_parser("chat", help="Regular chat mode")
        chat_parser.add_argument("--debug", action="store_true")

        suggested_models = ", ".join(f"{provider.lower()}/{model_tag}" for provider, model_tag in self._provider_model_pairs)

        chat_parser.add_argument(
            "--model",
            type=str,
            help=f"Model for the LLM (suggested models: {suggested_models})",
        )
        chat_parser.add_argument("--stt", action="store_true", help="Use Speech to Text mode for input")
        chat_parser.add_argument(
            "--no-markdown",
            action="store_true",
            help="Disable markdown highlighting for output",
        )
        chat_parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose logging (DEBUG level)",
        )

        return chat_parser

    def _build_simple_agent_parser(self, subparsers):
        simple_agent_parser = subparsers.add_parser("simple-agent", help="Simple agent mode")
        simple_agent_parser.add_argument("--debug", action="store_true")

        suggested_models = ", ".join(f"{provider.lower()}/{model_tag}" for provider, model_tag in self._provider_model_pairs)

        simple_agent_parser.add_argument(
            "--model",
            type=str,
            help=f"Model for the LLM (suggested models: {suggested_models})",
        )
        simple_agent_parser.add_argument("--stt", action="store_true", help="Use Speech to Text mode for input")
        simple_agent_parser.add_argument(
            "--no-markdown",
            action="store_true",
            help="Disable markdown highlighting for output",
        )
        simple_agent_parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose logging (DEBUG level)",
        )

        return simple_agent_parser

    def _build_research_parser(self, subparsers):
        research_parser = subparsers.add_parser("research", help="Deep research mode")
        research_parser.add_argument("--debug", action="store_true")

        suggested_models = ", ".join(f"{provider.lower()}/{model_tag}" for provider, model_tag in self._provider_model_pairs)

        research_parser.add_argument(
            "research_repo",
            help=("Path to research folder. You can specify the initial research name with :research-name"),
            type=str,
        )
        research_parser.add_argument(
            "--model",
            type=str,
            help=f"Model for the LLM (suggested models: {suggested_models})",
        )
        research_parser.add_argument("--stt", action="store_true", help="Use Speech to Text mode for input")
        research_parser.add_argument(
            "--no-markdown",
            action="store_true",
            help="Disable markdown highlighting for output",
        )
        research_parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose logging (DEBUG level)",
        )

        return research_parser

    def _build_utils_parser(self, subparsers):
        utils_parser = subparsers.add_parser("utils", help="Utility commands")
        utils_subparsers = utils_parser.add_subparsers(dest="utils_command", required=True)

        utils_parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose logging (DEBUG level)",
        )

        extract_pdf_parser = utils_subparsers.add_parser(
            "extract_pdf_pages",
            help="Extract pages from a PDF file. Will be saved as original_path/original_name_extracted.pdf",
        )
        extract_pdf_parser.add_argument("filepath", type=str, help="Path to the PDF file")
        extract_pdf_parser.add_argument("pages", type=str, help="Pages to extract (e.g. {1,4:5})")

        get_url_parser = utils_subparsers.add_parser("get_url", help="Get raw content from a URL using standard HTTP")
        get_url_parser.add_argument("url", type=str, help="URL to fetch content from")
        get_url_parser.add_argument(
            "--output",
            type=str,
            help="Output file path (default: url_hostname.txt)",
            default=None,
        )

        get_url_exa_parser = utils_subparsers.add_parser("get_url_exa", help="Get enhanced content from a URL using Exa API")
        get_url_exa_parser.add_argument("url", type=str, help="URL to fetch content from")
        get_url_exa_parser.add_argument(
            "--output",
            type=str,
            help="Output file path (default: url_hostname.txt)",
            default=None,
        )

        exa_search_parser = utils_subparsers.add_parser("exa_search", help="Search the web using Exa API")
        exa_search_parser.add_argument("query", type=str, help="Search query")
        exa_search_parser.add_argument(
            "--num_results",
            type=int,
            help="Number of results to return (default: 5)",
            default=5,
        )

        return utils_subparsers

    def _build_info_parser(self, subparsers):
        info_parser = subparsers.add_parser("info", help="Get command information")
        info_parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose logging (DEBUG level)",
        )

        info_subparsers = info_parser.add_subparsers(dest="info_command", required=True)

        info_subparsers.add_parser("list-assistant-commands", help="List all assistant commands")
        info_subparsers.add_parser("list-user-commands", help="List all user commands")

        return info_subparsers
