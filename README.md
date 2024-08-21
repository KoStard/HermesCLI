# Hermes: Multi-Model Chat Application

Hermes is a versatile command-line chat application that supports multiple AI models, allowing users to interact with various language models through a unified interface. Named after the messenger god of Greek mythology, Hermes efficiently relays messages between users and AI models.

## Features

- Support for multiple AI models:
  - Claude (Anthropic)
  - Bedrock Claude
  - Bedrock Claude 3.5
  - Bedrock Opus
  - Bedrock Mistral
  - Gemini (Google)
  - GPT-4 (OpenAI)
  - Ollama (Local models)
- File input support for context-aware conversations
- Image inputs for supported models
- Support for local models through Ollama integration
- Ability to append or update files based on AI responses
- Markdown rendering for formatted output
- Raw output option for unformatted responses
- Confirmation prompt to prevent unnecessary API calls
- Autocomplete support for model selection

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/KoStard/HermesCLI
   cd hermes
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your configuration file:
   Create a file at `~/.config/multillmchat/config.ini` with your API keys:
   ```ini
   [ANTHROPIC]
   api_key = your_anthropic_api_key

   [GEMINI]
   api_key = your_gemini_api_key

   [OPENAI]
   api_key = your_openai_api_key
   ```

4. Install the package in editable mode:
   ```
   pip install -e .
   ```

5. Enable autocomplete (optional):
   Add the following line to your shell configuration file (e.g., `.bashrc`, `.zshrc`):
   ```
   eval "$(register-python-argcomplete hermes)"
   ```
   For fish shell, run this:
   ```
   register-python-argcomplete --shell fish hermes > ~/.config/fish/completions/hermes.fish
   ```

## Usage

Basic usage:
```
hermes <model> [<file1> <file2> ... <fileN>]
```

Example:
```
hermes claude document1.txt document2.txt
```

After running the command, you will be prompted to enter your initial message or question.

### Command-line Options

- `--prompt`: Specify the initial prompt directly from the command line
- `--prompt-file`: Specify a file containing the initial prompt
- `--append` or `-a`: Append the AI's response to a specified file
- `--update` or `-u`: Update a specified file with the AI's response
- `--raw` or `-r`: Print the output without rendering markdown
- `--confirm-before-starting`: Prompt for confirmation before sending requests to the AI model

Examples:

Using --prompt:
```
hermes claude document1.txt document2.txt --prompt "Summarize these documents."
```

Using --prompt-file:
```
hermes claude document1.txt document2.txt --prompt-file my_prompt.txt
```

### Supported Models

- `claude`: Anthropic's Claude model
- `bedrock-claude`: AWS Bedrock Claude model
- `bedrock-claude-3.5`: AWS Bedrock Claude 3.5 model
- `bedrock-opus`: AWS Bedrock Claude 3 Opus model
- `bedrock-mistral`: AWS Bedrock Mistral model
- `gemini`: Google's Gemini model
- `openai`: OpenAI's GPT-4 model
- `ollama`: Local models through Ollama

## Configuration

### Ollama Setup

To use Ollama models:

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Run Ollama locally
3. In your `~/.config/multillmchat/config.ini`, add:
   ```ini
   [OLLAMA]
   model = llama2
   ```
   Replace `llama2` with your preferred model.

## Contributing

Contributions to Hermes are welcome! Please feel free to submit pull requests, create issues, or suggest new features.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Thanks to all the AI model providers for their APIs and services.
- [argcomplete](https://github.com/kislyuk/argcomplete) for providing autocompletion support.
