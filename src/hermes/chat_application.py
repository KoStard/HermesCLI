from typing import Dict, List, Optional, Type
import sys
from hermes.chat_models.base import ChatModel
from hermes.file_processors.base import FileProcessor
from hermes.prompt_builders.base import PromptBuilder
from hermes.ui.chat_ui import ChatUI
from hermes.utils import file_utils
from hermes.history_builder import HistoryBuilder
from hermes.context_providers.base import ContextProvider
from hermes.config import HermesConfig
import re


class ChatApplication:
    def __init__(
        self,
        model: ChatModel,
        ui: ChatUI,
        file_processor: FileProcessor,
        prompt_builder_class: Type[PromptBuilder],
        special_command_prompts: Dict[str, str],
        context_provider_classes: List[Type[ContextProvider]],
        hermes_config: HermesConfig,
    ):
        self.model = model
        self.ui = ui
        self.special_command_prompts = special_command_prompts
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
        special_command: Optional[Dict[str, str]] = None,
    ):
        if not special_command:
            special_command = {}
        self.model.initialize()

        # Check if input or output is coming from a pipe
        is_input_piped = not sys.stdin.isatty()
        is_output_piped = not sys.stdout.isatty()

        if is_input_piped or is_output_piped:
            self.handle_non_interactive_input_output(
                initial_prompt, special_command, is_input_piped, is_output_piped
            )
            return

        # Interactive mode
        try:
            self.handle_interactive_mode(initial_prompt, special_command)
        except KeyboardInterrupt:
            print("\nChat interrupted. Exiting gracefully...")

    def handle_interactive_mode(self, initial_prompt, special_command):
        if not self.make_first_request(initial_prompt, special_command):
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
                        provider.load_context_interactive(args_str)
                        self.history_builder.add_context(provider)
                        self.ui.display_status(f"Context added for /{command}")
                    else:
                        self.ui.display_status(f"Unknown command: /{command}")
                continue

            return user_input

    def make_first_request(
        self,
        initial_prompt: Optional[str] = None,
        special_command: Optional[Dict[str, str]] = None,
    ):
        self.history_builder.clear_regular_history()

        if initial_prompt:
            message = initial_prompt
        elif not self.add_special_command_to_prompt(special_command):
            print(
                "Chat started. Type 'exit', 'quit', or 'q' to end the conversation. Type '/clear' to clear the chat history."
            )
            message = self.get_user_input()

        response = self.send_message_and_print_output(message)

        if special_command:
            self.apply_special_command(special_command, response)
            return False
        return True

    def handle_non_interactive_input_output(
        self, initial_prompt, special_command, is_input_piped, is_output_piped
    ):
        if initial_prompt:
            message = initial_prompt
        if is_input_piped:
            self.history_builder.add_context(
                "text", sys.stdin.read().strip(), "piped_in_data"
            )
        elif not initial_prompt:
            message = self.ui.get_user_input()
        self.add_special_command_to_prompt(special_command)

        response = self.send_message_and_print_output(message)

        if special_command:
            if is_output_piped:
                raise Exception(
                    "Special command not supported for non-interactive output"
                )
            self.apply_special_command(special_command, response)

    def add_special_command_to_prompt(self, special_command: Dict[str, str]):
        if "append" in special_command:
            self.prompt_builder.add_text(
                self.special_command_prompts["append"].format(
                    file_name=file_utils.process_file_name(special_command["append"])
                )
            )
        elif "update" in special_command:
            self.prompt_builder.add_text(
                self.special_command_prompts["update"].format(
                    file_name=file_utils.process_file_name(special_command["update"])
                )
            )
        else:
            return False
        return True

    def apply_special_command(self, special_command: Dict[str, str], content: str):
        if "append" in special_command:
            file_utils.write_file(special_command["append"], "\n" + content, mode="a")
            self.ui.display_status(f"Content appended to {special_command['append']}")
        elif "update" in special_command:
            file_utils.write_file(special_command["update"], content, mode="w")
            self.ui.display_status(f"File {special_command['update']} updated")

    def send_message_and_print_output(self, user_input):
        try:
            self.history_builder.add_message("user", user_input)
            messages = self.history_builder.build_messages()
            response = self.ui.display_response(self.model.send_history(messages))
            self.history_builder.add_message("assistant", response)
            return response
        except KeyboardInterrupt:
            print()
            self.ui.display_status("Interrupted...")
            self.history_builder.pop_message()

    def clear_chat(self):
        self.model.initialize()
        self.history_builder.clear_regular_history()
        self.ui.display_status("Chat history cleared.")


[
    {
        "role": "user",
        "content": [
            {
                "text": '<document name="readme"># Hermes: Chat with AI Models, Files, and Execute Workflows\n\nHermes is a powerful command-line tool that enables you to interact with various AI models, process files, and execute complex workflows. Named after the messenger god in Greek mythology, Hermes facilitates seamless communication between you, AI models, and your local files.\n\n## What Hermes Can Do\n\n- Chat with a variety of AI models:\n  - Claude (Anthropic)\n  - Bedrock Claude 3.5\n  - Gemini (Google)\n  - GPT-4 (OpenAI)\n  - Ollama (Local models)\n  - DeepSeek (DeepSeek AI)\n  - And many more...\n- File input support for context-aware conversations\n- Image inputs for supported models\n- URL input to read and pass to the LLM\n- Support for local models through Ollama integration\n- Ability to append or update files based on AI responses\n- Markdown rendering for formatted output\n- Execute complex workflows defined in YAML files\n- Extension model to support custom context providers (e.g. custom parsers for different file formats, web pages, etc.)\n- Pipe the input into the LLM\n- Pipe the output from the LLM\n\n## Installation\n\n1. Clone the repository:\n   ```\n   git clone https://github.com/KoStard/HermesCLI\n   cd HermesCLI\n   ```\n\n2. Install the package in editable mode:\n   ```\n   pip install -e .\n   ```\n\nAfter installation, set up your configuration file:\n\n1. Create a file named `config.ini` in the following location:\n   - On Unix-like systems (Linux, macOS): `~/.config/multillmchat/config.ini`\n   - On Windows: `C:\\Users\\YourUsername\\.config\\multillmchat\\config.ini`\n\n2. Add your API keys and default model to the config file:\n   ```ini\n   [BASE]\n   model = claude\n\n   [ANTHROPIC]\n   api_key = your_anthropic_api_key\n\n   [GEMINI]\n   api_key = your_gemini_api_key\n\n   [OPENAI]\n   api_key = your_openai_api_key\n\n   [DEEPSEEK]\n   api_key = your_deepseek_api_key\n   model = deepseek-coder\n```\n   \n   You can set any supported model as the default in the `[BASE]` section.\n\n   Note: The application will create the necessary directories if they don\'t exist.\n\n\n## Usage\n### Basic usage\n\nBasic usage:\n```\nhermes [--model MODEL] [&lt;file1&gt; &lt;file2&gt; ... &lt;fileN&gt;]\n```\n\nExample:\n```\nhermes document1.txt document2.txt\n```\n\nHermes will use the default model specified in your config file. If you want to use a different model, you can specify it with the --model option:\n\n```\nhermes --model claude document1.txt document2.txt\n```\n\nAfter running the command, you will be prompted to enter your initial message or question.\n\n### Command-line Options\n\n- `--model`: Specify the AI model to use (e.g., claude, bedrock-claude, gemini, openai, ollama, deepseek)\n- `--prompt`: Specify the initial prompt directly from the command line\n- `--prompt-file`: Specify a file containing the initial prompt\n- `--append` or `-a`: Append the AI\'s response to a specified file\n- `--update` or `-u`: Update a specified file with the AI\'s response\n- `--pretty`: Print the output by rendering markdown\n- `--workflow`: Specify a workflow YAML file to execute\n- `--image`: Pass an image to the LLM (can be used multiple times)\n- `--text`: Additional text to be included with prompts (can be used multiple times)\n- `--url`: Pass a URL, that will be opened, parsed and passed to the LLM  (can be used multiple times)\n\nIf you pipe into the input of hermes, or pipe the output of hermes, it will call the LLM only once, print the output and exit.\n\nYou can also implement your own custom context providers, which will be accessible from CLI with your own custom arguments.\n#### Configuring custom context providers\nCreate a sub-folder in `~/.config/hermes/extra_context_providers/`, you can name it something about the group of extensions you are adding, or just call it `extensions`.\nThen inside `~/.config/hermes/extra_context_providers/&lt;your_extensions_folder&gt;/` create a python file (use snake_case for the name of the file).\nThere create a class, that implements `hermes.context_providers.base.ContextProvider`.\n\nExample:\n```python\n# /home/kostard/.config/hermes/extra_context_providers/my_test/test.py\n\nfrom argparse import ArgumentParser\nfrom hermes.context_providers.base import ContextProvider\nfrom hermes.config import HermesConfig\nfrom hermes.prompt_builders.base import PromptBuilder\n\nclass TestContextProvider(ContextProvider):\n    @staticmethod\n    def add_argument(parser: ArgumentParser):\n        parser.add_argument(\'--test\', help="My test context provider")\n\n    def load_context(self, config: HermesConfig):\n\t    # HermesConfig contains all the arguments parsed from CLI, so the --test is present here\n        # This is my opportunity to load and store some context. If I need to make network requests, I can do it here.\n        self.test = config.get(\'test\', \'default_test\')\n\n    def add_to_prompt(self, prompt_builder: PromptBuilder):\n        # This is my opportunity to add something to the prompt\n        prompt_builder.add_text(self.test, name="test")\n\n```\nNow we\'ll see:\n```sh\nhermes --help\n# ...\n#   --test TEST           My test context provider\n\nhermes --test "My secret is 1234" --prompt "what is my secret?"\n# Your secret is "1234".\n```\n#### Examples:\n\nSummarise a document, and continue chatting about it:\n```sh\nhermes --model claude README.md --prompt "Summarise this document into 1 paragraph"\n# Hermes is a versatile command-line tool that enables users to interact with various AI models, process files, and execute complex workflows. It supports a wide range of AI models, including Claude, GPT-4, Gemini, and local models through Ollama integration. Hermes offers features such as file and image input support, URL parsing, the ability to append or update files based on AI responses, markdown rendering, and the execution of workflows defined in YAML files. Users can easily install Hermes, configure API keys, and use it with various command-line options to chat with AI models, process documents, and run complex tasks. The tool also supports piping input and output, making it a powerful and flexible solution for AI-assisted tasks and automation.\n# ----\n# You:\n```\n\nPiping the output:\n```sh\nhermes --prompt "Tell me a fact about space for my curiosity" | cat\n# Sure! Here\'s a fascinating fact about space:\n# \n# The Sun, which is the center of our solar system, is made up of about 98% hydrogen and helium. It has a diameter of approximately 1.39 million kilometers (864,000 miles), which is about 109 times the diameter of Earth. Despite its immense size, the Sun is considered an average-sized star in the vastness of the universe.\n```\n\nPiping input:\n```sh\necho "Hello, how are you?" | hermes\n# Hello! I\'m here to help. How can I assist you today?\n```\n\nUsing --workflow:\n```\nhermes --workflow my_workflow.yaml --model claude\n```\n\n### Supported Models\n\n- `claude`: Anthropic\'s Claude model\n- `bedrock-claude`: AWS Bedrock Claude model\n- `bedrock-claude-3.5`: AWS Bedrock Claude 3.5 model\n- `bedrock-opus`: AWS Bedrock Claude 3 Opus model\n- `bedrock-mistral`: AWS Bedrock Mistral model\n- `gemini`: Google\'s Gemini model\n- `openai`: OpenAI\'s GPT-4 model\n- `ollama`: Local models through Ollama\n- `deepseek`: DeepSeek AI\'s models\n- `groq`: You specify which groq model in the config file\n\n## Configuration\n\n### Bedrock Setup\n\nTo use AWS Bedrock models:\n\nHermes will rely on your AWS credentials, which can be provided through:\n1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN)\n2. The AWS credentials file (~/.aws/credentials)\n\nMake sure you have the necessary permissions to access Bedrock services in your AWS account.\n\n### Ollama Setup\n\nTo use Ollama models:\n\n1. Install Ollama from [ollama.ai](https://ollama.ai)\n2. Run Ollama locally\n3. In your `~/.config/multillmchat/config.ini`, add:\n   ```ini\n   [OLLAMA]\n   model = llama2\n```\n   Replace `llama2` with your preferred model.\n\n### DeepSeek Setup\n\nTo use DeepSeek models:\n\n1. Sign up for an account at [DeepSeek AI](https://platform.deepseek.com/)\n2. Obtain your API key from the DeepSeek platform\n3. In your `~/.config/multillmchat/config.ini`, add:\n   ```ini\n   [DEEPSEEK]\n   api_key = your_deepseek_api_key\n   base_url = https://api.deepseek.com\n   model = deepseek-coder\n```\n   You can replace `deepseek-coder` with other available DeepSeek models if desired.\n\n## Contributing\n\nContributions to Hermes are welcome! Please feel free to submit pull requests, create issues, or suggest new features.\n\n## License\n\nThis project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.\n\n## Using Workflows\n\nHermes now supports executing complex workflows defined in YAML files. Here\'s a simple example of how to use workflows:\n\n1. Create a YAML file defining your workflow (e.g., `my_workflow.yaml`):\n\n```yaml\nmy_root_task:\n  type: sequential\n  tasks:\n    task1:\n      type: llm\n      prompt: "Hello, world!"\n    task2:\n      type: shell\n      command: "echo \'Task completed\'"\n```\n\n2. Run the workflow using the Hermes CLI:\n\n```\nhermes --workflow my_workflow.yaml --model claude\n```\n\nThis workflow does the following:\n1. Sends a prompt to the LLM to summarize some input text.\n2. Saves the summary to a file using a shell command.\n3. Generates questions based on the summary using the LLM.\n\nYou can define more complex workflows with multiple LLM and shell tasks, using the output of one task as input for another. The new structure allows for nesting sequential tasks, providing more flexibility in workflow design.\n\nExample of a nested sequential task:\n\n```yaml\ntype: sequential\ntasks:\n  - id: task1\n    type: llm\n    prompt: "Summarize the following text: {input_text}"\n    output_mapping:\n      summary: result.response\n\n  - id: nested_tasks\n    type: sequential\n    tasks:\n      - id: subtask1\n        type: shell\n        command: "echo \'Summary: {summary}\' &gt; summary.txt"\n\n      - id: subtask2\n        type: llm\n        prompt: "Generate 3 questions based on this summary: {summary}"\n        output_mapping:\n          questions: result.response\n\n  - id: task3\n    type: shell\n    command: "echo \'Questions: {questions}\' &gt;&gt; summary.txt"\n```\n\nThis structure allows for more complex and organized workflows, with the ability to group related tasks together using nested sequential tasks.\n\n## License\n\nThis project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.\n</document>'
            },
            {
                "text": '<document name="tasks">- allow adding context mid-way while running the app\n- history recovery feature\n- improve the model configuration, instead of if/else, convert it to separate entries\n- move config to ~/.config/hermes/\n- error handling for the LLM requests, if it fails the message should just be discarded and go back\n- special commands as context providers, for now with a hardcoded action in the chat application\n- when loading extensions, they might fail, it should not crash the app, instead it should log the error and move on\n- allow changing the model midway\n</document>'
            },
            {"text": "What is this about?\n"},
        ],
    },
    {
        "role": "assistant",
        "content": "This document is about Hermes, a powerful command-line tool for interacting with various AI models, processing files, and executing complex workflows. Here's a summary of the key points:\n\n1. Hermes allows users to chat with multiple AI models, including Claude, GPT-4, Gemini, and local models through Ollama integration.\n\n2. It supports file input for context-aware conversations, image inputs, URL parsing, and the ability to append or update files based on AI responses.\n\n3. The tool can execute complex workflows defined in YAML files and supports custom context providers for extending functionality.\n\n4. Hermes offers various command-line options for specifying models, prompts, file operations, and workflow execution.\n\n5. It supports piping input and output, making it flexible for integration with other command-line tools.\n\n6. The document provides installation instructions, usage examples, and configuration details for various AI models and services.\n\n7. Hermes can be customized with additional context providers, allowing users to extend its capabilities.\n\n8. The tool supports executing complex workflows defined in YAML files, enabling users to chain multiple tasks involving AI models and shell commands.\n\n9. Hermes is open-source and licensed under the Apache License 2.0, welcoming contributions from the community.\n\nOverall, Hermes is a versatile and powerful tool for AI-assisted tasks, file processing, and workflow automation through a command-line interface.",
    },
    {"role": "user", "content": [{"text": "Then what is tasks.md about?\n"}]},
]
