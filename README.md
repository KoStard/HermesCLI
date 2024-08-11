# Hermes: Multi-Model Chat Application

Hermes is a versatile command-line chat application that supports multiple AI models, allowing users to interact with various language models through a unified interface. Named after the messenger god of Greek mythology, Hermes efficiently relays messages between users and AI models.

## Features

- Support for multiple AI models:
  - Claude (Anthropic)
  - Bedrock Claude
  - Bedrock Mistral
  - Gemini (Google)
  - GPT-4 (OpenAI)
- File input support for context-aware conversations
- Image inputs for supported models
- Ability to append or update files based on AI responses
- Markdown rendering for formatted output
- Raw output option for unformatted responses
- Confirmation prompt to prevent unnecessary API calls

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

4. Make it executable:
   ```
   chmod +x hermes.py
   ```

5. Copy to `/usr/local/bin/` for convenience
    ```
    sudo ln -s /absolute/path/hermes.py /usr/local/bin/hermes
    ```

## Usage

Basic usage:
```
hermes <model> <file1> <file2> ... <fileN> <prompt>
```

Example:
```
hermes claude \
    document1.txt \
    document2.txt \
    "Summarize these documents."
```

### Command-line Options

- `--append` or `-a`: Append the AI's response to a specified file
- `--update` or `-u`: Update a specified file with the AI's response
- `--raw` or `-r`: Print the output without rendering markdown
- `--confirm-before-starting`: Prompt for confirmation before sending requests to the AI model

### Supported Models

- `claude`: Anthropic's Claude model
- `bedrock-claude`: AWS Bedrock Claude model
- `bedrock-mistral`: AWS Bedrock Mistral model
- `gemini`: Google's Gemini model
- `openai`: OpenAI's GPT-4 model

## Contributing

Contributions to Hermes are welcome! Please feel free to submit pull requests, create issues, or suggest new features.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Thanks to all the AI model providers for their APIs and services.
