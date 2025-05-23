# Hermes

Hermes is an extendable command-line interface (CLI) for interacting with Large Language Models (LLMs). It provides a flexible and powerful way to leverage AI capabilities directly from your terminal, with support for multiple model providers, multimedia input, and specialized research workflows.

## Features

- **Multiple LLM Providers**: Supports OpenAI, Anthropic, Google Gemini, Groq, DeepSeek, SambaNova, OpenRouter, AWS Bedrock, and XAI
- **Multimedia Input**: Handle images, audio, video, PDFs, URLs, and various document formats
- **Deep Research Mode**: Advanced research assistant with hierarchical problem-solving and artifact management
- **Extensible Architecture**: Add custom commands and functionality through extensions
- **Conversation History**: Save and load chat sessions
- **Speech-to-Text**: Voice input support via Groq API
- **File Operations**: LLM can create, modify, and manage files with safety features
- **Web Integration**: Fetch and analyze web content with Exa API integration
- **Debug Mode**: Visual debugging interface to see what the LLM receives

## Getting Started

### Installation

Hermes requires Python 3.10 or later. Install using uv (recommended) or pip:

```bash
# Using uv (recommended)
uv tool install git+https://github.com/KoStard/HermesCLI --upgrade --python 3.11

# Using pip
pip install --upgrade git+https://github.com/KoStard/HermesCLI.git
```

### Configuration

Before using Hermes, you'll need to configure your API keys. Hermes looks for its configuration file (`config.ini`) and `extensions` directory in a specific location based on your operating system.

**Configuration Directory Locations:**

*   **Linux & macOS:** `~/.config/hermes/`
*   **Windows:** `C:\Users\<YourUsername>\AppData\Roaming\hermes\`
    *(Note: The exact Windows path might vary slightly. `%APPDATA%\hermes\` is the general location)*

**Setup:**

First, ensure the configuration directory for your OS exists:

*   **Linux & macOS:** `mkdir -p ~/.config/hermes/`
*   **Windows:** Create the `hermes` folder in your `%APPDATA%` directory (e.g., `C:\Users\<YourUsername>\AppData\Roaming\hermes\`)

Then, inside that directory, create a file named `config.ini` with the following format:

```ini
[BASE]
model = OPENAI/gpt-4o  ; Default model (use hermes chat --help to see available models)

[OPENAI]
api_key = YOUR_OPENAI_API_KEY
; base_url = http://localhost:1234/v1  ; Optional: for OpenAI-compatible endpoints

[ANTHROPIC]
api_key = YOUR_ANTHROPIC_API_KEY

[GEMINI]
api_key = YOUR_GEMINI_API_KEY

[GROQ]
api_key = YOUR_GROQ_API_KEY

[DEEPSEEK]
api_key = YOUR_DEEPSEEK_API_KEY

[SAMBANOVA]
api_key = YOUR_SAMBANOVA_API_KEY

[OPENROUTER]
api_key = YOUR_OPENROUTER_API_KEY

[BEDROCK]
aws_region = YOUR_AWS_REGION
aws_profile_name = YOUR_AWS_PROFILE_NAME  ; Optional

[XAI]
api_key = YOUR_XAI_API_KEY

[EXA]
api_key = YOUR_EXA_API_KEY  ; Optional: for enhanced web search
```

Replace `YOUR_API_KEY` with your actual API keys for each provider.

### Basic Usage

Start a conversation with your default model:

```bash
hermes chat
```

**Advanced Usage:**

```bash
# Use a specific model
hermes chat --model ANTHROPIC/claude-3-5-sonnet-20241022

# Enable Deep Research mode for complex problem-solving
hermes chat --deep-research /path/to/research/folder

# Debug mode (see what the LLM receives)
hermes chat --debug

# Voice input (requires Groq API)
hermes chat --stt

# Pass files and commands directly
hermes chat file1.txt file2.py --image_url "https://example.com/image.jpg" --text "Analyze these files"
```

### User Commands

Hermes supports several user commands to enhance your interaction with LLMs:

| Command                                           | Description                                                                                                                                 |
| :------------------------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------ |
| `/clear`                                          | Clear the conversation history.                                                                                                             |
| `/image <image_path>`                             | Add an image to the conversation.                                                                                                           |
| `/image_url <image_url>`                          | Add an image from a URL to the conversation.                                                                                                |
| `/audio <audio_filepath>`                         | Add an audio file to the conversation.                                                                                                      |
| `/video <video_filepath>`                         | Add a video file to the conversation.                                                                                                      |
| `/pdf <pdf_filepath> {<page_num>, <start>:<end>}` | Add a PDF file to the conversation. Optionally, specify pages using individual numbers or ranges (e.g., `1, 3:5`).<br>This is for LLM models that support direct PDF embedding (e.g. Claude 3.5 Sonnet, Gemini models, etc). In this case they also look at the pages as images.                        |
| `/textual_file <text_filepath>`                   | Add a textual file (e.g., .txt, .md, .pdf, .docx) to the conversation. Supported formats include plain text (with any extension/format), PDF, DOC, PowerPoint, Excel. If you want to attach a PDF file, but only its text content, use this. |
| `/url <url>`                                      | Add a URL to the conversation.                                                                                                             |
| `/save_history <filepath>`                       | Save the conversation history to a file.                                                                                                   |
| `/load_history <filepath>`                       | Load a conversation history from a file.                                                                                                   |
| `/text <text>`                                    | Add text to the conversation.                                                                                                               |
| `/exit`                                           | Exit the application.                                                                                                                      |

### CLI Commands

Pass commands directly via CLI arguments:

```bash
# Analyze multiple files with an image
hermes chat file1.py file2.md --image_url "https://example.com/chart.png" --text "Analyze the code and chart"

# Files are automatically treated as textual content
hermes chat document.pdf report.docx  # Extracts text content
```

### LLM File Operations

The LLM can interact with files using structured commands with `<<<command>>>` blocks:

| Command | Description | Example |
|---------|-------------|---------|
| `create_file` | Create new files with confirmation prompts | `<<<create_file`<br>`///path`<br>`example.txt`<br>`///content`<br>`File content here`<br>`>>>` |
| `markdown_update_section` | Update specific markdown sections | `<<<markdown_update_section`<br>`///path`<br>`README.md`<br>`///section_path`<br>`Features`<br>`///content`<br>`New content`<br>`>>>` |
| `append_file` | Add content to end of files | `<<<append_file`<br>`///path`<br>`log.txt`<br>`///content`<br>`New entry`<br>`>>>` |
| `prepend_file` | Add content to beginning of files | `<<<prepend_file`<br>`///path`<br>`notes.txt`<br>`///content`<br>`Header info`<br>`>>>` |

**Safety Features:**
- Automatic backups before overwriting existing files
- Confirmation prompts for destructive operations  
- Sandbox directory (`/tmp/hermes_sandbox/`) for unspecified locations
- Relative and absolute path support

## Extending Hermes

Hermes can be extended by adding custom commands. Extensions are loaded from the `extensions` subdirectory within the configuration root directory specified in the Configuration section above for your OS. Each extension should be in its own subdirectory and contain an `extension.py` file.

### Extension Structure

Example for Linux/macOS:
```
~/.config/hermes/
├── config.ini
└── extensions/
    └── my_extension/
        └── extension.py
```

Example for Windows:
```
C:\Users\<YourUsername>\AppData\Roaming\hermes\
├── config.ini
└── extensions\
    └── my_extension\
        └── extension.py
```


### Example Extension

Here's an example of an `extension.py` file that you can put inside an `example_extension` subdirectory within your `extensions` folder:

```python
from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.event import MessageEvent
from hermes.message import TextMessage

def get_user_extra_commands():
    """
    These are the commands that the user will be able to trigger from CLI arguments or during the chat with slash commands.
    Define the command label with a single slash (/command).
    """
    return [
        ControlPanelCommand(
            command_id="example_command",
            short_description="Example Command",
            command_label="/example_command",
            description="An example custom command",
            parser=lambda line: MessageEvent(TextMessage(author="user", text="This is an example command response that the LLM will receive."))
        )
    ]

def get_llm_extra_commands():
    """
    These are the commands that the LLM will be able to trigger during the chat with tripple-slash commands.
    Define the command label with a tripple-slash (///command).
    If you want to allow multiline input, you can have a special closing tag, like ///end_file.
    For more details check the hermes/interface/control_panel/llm_control_panel.py
    """
    return []

def get_utils_builders():
    """
    These are utility commands that will be available through the CLI.
    Each builder function should take an ArgumentParser._SubParsersAction as input
    and return a visitor function that will be called with the parsed arguments.
    """
    def setup_example_util(subparsers):
        parser = subparsers.add_parser(
            "example-util",
            help="An example utility command"
        )
        parser.add_argument("arg1", help="First argument")
        
        def visitor(cli_args, config):
            if cli_args.utils_command != "example-util":
                return
            print(f"Running example util with arg: {cli_args.arg1}")
        
        return visitor

    return [setup_example_util]
```

## Available Commands

View all available commands:

```bash
# List user commands (what you can use)
hermes info list-user-commands

# List LLM commands (what the AI can use)
hermes info list-assistant-commands
```

**Key User Commands:**
- `/image`, `/audio`, `/video` - Share media files
- `/pdf`, `/textual_file` - Share documents  
- `/url` - Share web content
- `/save_history`, `/load_history` - Manage conversations
- `/clear` - Reset conversation
- `/tree` - Show directory structure

**Utility Commands:**
```bash
# Extract specific pages from PDFs
hermes utils extract_pdf_pages document.pdf "{1,3:5}"

# Fetch web content
hermes utils get_url https://example.com

# Enhanced web search (requires Exa API)
hermes utils exa_search "AI research papers"
```

## Deep Research Mode

For complex research tasks, use the Deep Research Assistant:

```bash
hermes chat --deep-research /path/to/research/folder
```

**Features:**
- Hierarchical problem decomposition
- Artifact management and tracking
- Research project organization
- Status reporting and progress tracking
- Knowledge base integration
- Structured research workflows

The research folder will contain organized files, reports, and artifacts generated during the research process.

## Contributing

Contributions to Hermes are welcome! If you have an idea for a new feature or an improvement, feel free to open an issue or submit a pull request.

## License

Hermes is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Key Dependencies

Hermes is built with these excellent open-source libraries:

- **AI Providers:** Anthropic, OpenAI, Google Generative AI, Groq, AWS Boto3
- **Document Processing:** MarkItDown, PyPDF2
- **Interface:** prompt-toolkit, Pygments, InquirerPy  
- **Audio:** SoundDevice, SoundFile
- **Web:** Requests, Exa-py
- **Templates:** Mako
- **Utilities:** NumPy, PyYAML, Tenacity

Thanks to all contributors and maintainers!
