# Hermes: Chat with AI Models, Files, and Execute Workflows

Hermes is a powerful command-line tool that enables you to interact with various AI models, process files, and execute complex workflows. Named after the messenger god in Greek mythology, Hermes facilitates seamless communication between you, AI models, and your local files.

## What Hermes Can Do

- Chat with a variety of AI models:
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
- **NEW: Execute complex workflows defined in YAML files**

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
   Create a file at `~/.config/multillmchat/config.ini` with your API keys and default model:
   ```ini
   [DEFAULT]
   model = claude

   [ANTHROPIC]
   api_key = your_anthropic_api_key

   [GEMINI]
   api_key = your_gemini_api_key

   [OPENAI]
   api_key = your_openai_api_key
   ```
   
   You can set any supported model as the default in the `[DEFAULT]` section.

4. Install the package in editable mode:
   ```
   pip install -e .
   ```

## Usage

Basic usage:
```
hermes [--model MODEL] [<file1> <file2> ... <fileN>]
```

Example:
```
hermes document1.txt document2.txt
```

Hermes will use the default model specified in your config file. If you want to use a different model, you can specify it with the --model option:

```
hermes --model claude document1.txt document2.txt
```

After running the command, you will be prompted to enter your initial message or question.

### Command-line Options

- `--model`: Specify the AI model to use (e.g., claude, bedrock-claude, gemini, openai, ollama)
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

### Bedrock Setup

To use AWS Bedrock models:

Hermes will rely on your AWS credentials, which can be provided through:
1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN)
2. The AWS credentials file (~/.aws/credentials)

Make sure you have the necessary permissions to access Bedrock services in your AWS account.

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
