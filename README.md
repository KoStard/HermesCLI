# Hermes

Hermes is an extendable command-line interface (CLI) designed to interact with Large Language Models (LLMs). It aims to provide a flexible and powerful way to leverage the capabilities of LLMs directly from your terminal. Whether you're a developer, researcher, or just an AI enthusiast, Hermes offers a streamlined experience for interacting with state-of-the-art language models.

## Features

- **Easy Interaction with Multiple LLMs**: Supports various LLMs, allowing you to switch between models seamlessly.
- **Extendable Architecture**: Built with extensibility in mind, allowing users to add custom commands and functionalities.
- **CLI-First Design**: Optimized for the command line, providing a fast and efficient way to work with LLMs.
- **Conversation History**: Keeps track of your conversation history, allowing you to pick up where you left off.
- **Advanced Media Input**: Supports various media types, including images, audio, video, PDFs, URLs, and textual files.
- **Configurable**: Easily configure API keys and settings through a simple configuration file.
- **Speech-to-Text Input**: Optionally use speech-to-text for a more interactive experience.

## Getting Started

### Installation

To install Hermes, you need to have Python 3.10 or later installed on your system. Then, you can install Hermes using pip:

```bash
pip install --upgrade git+https://github.com/KoStard/HermesCLI.git
# or with uv
uv tool install git+https://github.com/KoStard/HermesCLI --upgrade --python 3.10
```

### Configuration

Before using Hermes, you'll need to configure your API keys for the LLMs you intend to use. Create a configuration file at `~/.config/hermes/config.ini` with the following format:

```ini
[BASE]
model = OPENAI/gpt-4o ; Or whatever model you want to use. To see the list of suggested models, check hermes --help

[OPENAI]
api_key = YOUR_OPENAI_API_KEY

[GROQ]
api_key = YOUR_GROQ_API_KEY

[ANTHROPIC]
api_key = YOUR_ANTHROPIC_API_KEY

[GEMINI]
api_key = YOUR_GEMINI_API_KEY

[DEEPSEEK]
api_key = YOUR_DEEPSEEK_API_KEY

[SAMBANOVA]
api_key = YOUR_SAMBANOVA_API_KEY

[OPENROUTER]
api_key = YOUR_OPENROUTER_API_KEY

[BEDROCK]
aws_region = YOUR_AWS_REGION  ; Will use your default profile in you AWS credentials

[XAI]
api_key = YOUR_XAI_API_KEY
```

Replace `YOUR_API_KEY` with your actual API keys for each provider.

### Basic Usage

To start a conversation with the default LLM model (from the configuration file), simply run:

```bash
hermes chat
```

You can also override the model using the `--model` flag:

```bash
hermes chat --model OPENAI/gpt-4o
```

For debugging purposes, you can use the `--debug` flag to spawn a separate terminal window that will act as the LLM, this way you can see what the LLM "sees":

```bash
hermes chat --debug
```

To use speech-to-text input, use the `--stt` flag (requires your Groq API keys):

```bash
hermes chat --stt
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

### Using CLI Arguments

You can also pass user commands directly as CLI arguments:

```bash
hermes chat file1 file2 file3 --image_url "https://example.com/image.jpg" --text "Describe this image"
```

The files provided are treated as `--textual_file`.

### LLM Commands

The same way as you (the user) has access to commands in Hermes, the LLM has access to commands as well. These commands allow the LLM to interact with the file system in a controlled manner. Below is a table of available LLM commands:

| Command | Description | Example |
|---------|-------------|---------|
| `///create_file` | Creates a new file with specified content. If the file exists, it will ask for confirmation before overwriting. | `///create_file example.txt`<br>This is some content<br>`///end_file` |
| `///markdown_update_section` | Updates a specific section in a markdown file. The section is identified by its header path. | `///markdown_update_section README.md Features`<br>New feature description<br>`///end_section` |
| `///markdown_append_section` | Appends content to a specific section in a markdown file. The content is added at the end of the specified section. | `///markdown_append_section README.md Features`<br>Additional feature description<br>`///end_section` |
| `///append_file` | Appends content to the end of an existing file. Creates the file if it doesn't exist. | `///append_file log.txt`<br>New log entry<br>`///end_file` |
| `///prepend_file` | Adds content to the beginning of an existing file. Creates the file if it doesn't exist. | `///prepend_file notes.txt`<br>Important note<br>`///end_file` |

**Important Notes:**
1. The LLM knows the current working directory and can create files with relative and absolute paths.
2. For safety, if a file already exists, the LLM will ask for confirmation before overwriting and will create a backup in `/tmp/hermes/backups/{filename}_{timestamp}.bak`.
3. The LLM is asked to only use these commands when explicitly asked by the user, but it might sometimes show initiative.
4. When creating files, if no specific location is mentioned, files will be created in Hermes' sandbox under `/tmp/hermes_sandbox/`.

## Extending Hermes

Hermes can be extended by adding custom commands. Extensions are loaded from the `~/.config/hermes/extensions/` directory. Each extension should be in a separate subdirectory and contain an `extension.py` file.

### Extension Structure

```
~/.config/hermes/extensions/
└── my_extension/
    └── extension.py
```

### Example Extension

Here's an example of an `extension.py` file that you can put to `~/.config/hermes/extensions/example_extension/`:

```python
from hermes.interface.control_panel.base_control_panel import ControlPanelCommand
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
```

## Listing the available commands

Hermes provides commands for both users and LLMs. You can list all available commands using the following CLI commands:

### Listing User Commands

To list all available user commands, run:

```bash
hermes info list-user-commands
```

Example output:

```txt
Command ID      | Description
----------------+----------------------------
audio           | Share an audio file
clear           | Clear chat history
example_command | Example Command       <--- Notice the example command we added in the extension
exit            | Exit Hermes
image           | Share an image file
image_url       | Share an image via URL
load_history    | Load chat history
pdf             | Share a PDF file
save_history    | Save chat history
text            | Send a text message
textual_file    | Share a text-based document
tree            | Show directory structure
url             | Share a URL◊
video           | Share a video file
```

### Listing LLM Commands

To list all available LLM commands, run:

```bash
hermes info list-assistant-commands
```

Example output:

```txt
Command ID              | Description
------------------------+---------------------------------
append_file             | Append to file end
create_file             | Create a new file
markdown_append_section | Add content to markdown section
markdown_update_section | Replace markdown section content
prepend_file            | Add to file beginning
```

These commands provide a comprehensive list of all available commands with their descriptions, helping users and LLMs understand the available functionality.

## Contributing

Contributions to Hermes are welcome! If you have an idea for a new feature or an improvement, feel free to open an issue or submit a pull request.

## License

Hermes is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Acknowledgments

Hermes is built using several excellent open-source libraries, including:

- [Anthropic](https://www.anthropic.com/)
- [Boto3](https://aws.amazon.com/sdk-for-python/)
- [Google Generative AI](https://ai.google.dev/)
- [LiteLLM](https://litellm.ai/)
- [MarkItDown](https://github.com/microsoft/markitdown/)
- [Mistune](https://mistune.lepture.com/)
- [NumPy](https://numpy.org/)
- [OpenAI](https://openai.com/)
- [prompt-toolkit](https://python-prompt-toolkit.readthedocs.io/)
- [Pygments](https://pygments.org/)
- [PyPDF2](https://pypdf2.readthedocs.io/)
- [Requests](https://requests.readthedocs.io/)
- [SoundDevice](https://python-sounddevice.readthedocs.io/)
- [SoundFile](https://pysoundfile.readthedocs.io/)

Thank you to all the contributors and maintainers of these projects!
