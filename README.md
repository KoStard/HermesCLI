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
uv tool install git+https://github.com/KoStard/HermesCLI --upgrade
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
```

Replace `YOUR_API_KEY` with your actual API keys for each provider.

### Basic Usage

To start a conversation with the default LLM, simply run:

```bash
hermes
```

You can also specify a particular model using the `--model` flag:

```bash
hermes --model OPENAI/gpt-4o
```

For debugging purposes, you can use the `--debug` flag to spawn a separate terminal window that will act as the LLM, this way you can see what the LLM "sees":

```bash
hermes --debug
```

To use speech-to-text input, use the `--stt` flag (requires your Groq API keys):

```bash
hermes --stt
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
| `/pdf <pdf_filepath> {<page_num>, <start>:<end>}` | Add a PDF file to the conversation. Optionally, specify pages using individual numbers or ranges (e.g., `1, 3:5`).                        |
| `/textual_file <text_filepath>`                   | Add a textual file (e.g., .txt, .md, .pdf, .docx) to the conversation. Supported formats include plain text, PDF, DOC, PowerPoint, Excel. |
| `/url <url>`                                      | Add a URL to the conversation.                                                                                                             |
| `/save_history <filepath>`                       | Save the conversation history to a file.                                                                                                   |
| `/load_history <filepath>`                       | Load a conversation history from a file.                                                                                                   |
| `/text <text>`                                    | Add text to the conversation.                                                                                                               |
| `/exit`                                           | Exit the application.                                                                                                                      |

### Using CLI Arguments

You can also pass user commands directly as CLI arguments:

```bash
hermes --image_url "https://example.com/image.jpg" --text "Describe this image"
```

Arguments are processed in the order they are provided.

### LLM Commands

The same way as you (the user) has access to commands in Hermes, the LLM has access to commands as well.
Currently, the only implemented command is the `///create_file` command.
The LLM knows the current working directory, and will see the paths of the attached files. It can create files with relative and absolute paths.
To make the usage safer, in case the file already exists, before overwriting, it asks the user to confirm and backs up the file in `/tmp/hermes/backups/{filename}_{timestamp}.bak`.

## Extending Hermes

Hermes can be extended by adding custom commands. Extensions are loaded from the `~/.config/hermes/extensions/` directory. Each extension should be in a separate subdirectory and contain an `extension.py` file.

### Extension Structure

```
~/.config/hermes/extensions/
└── my_extension/
    └── extension.py
```

### Example Extension

Here's an example of an `extension.py` file:

```python
from hermes.interface.control_panel.base_control_panel import ControlPanelCommand
from hermes.event import MessageEvent
from hermes.message import TextMessage

def get_user_extra_commands():
    return [
        ControlPanelCommand(
            command_label="/my_command",
            description="My custom command",
            parser=lambda line: MessageEvent(TextMessage(author="user",text="We are playing ping pong. It's my turn: ping."))
        )
    ]

def get_llm_extra_commands():
    return []
```

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
- [Markdownify](https://github.com/matthewwithanm/python-markdownify)
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
