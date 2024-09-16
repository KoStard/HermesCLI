# Hermes: Your AI-Powered Command-Line Assistant

Hermes is a powerful command-line tool that allows you to interact with various AI models, process files, and enhance your productivity. Named after the messenger god in Greek mythology, Hermes facilitates seamless communication between you and AI models.

## What is Hermes?

Hermes is a versatile application that enables you to:

- Chat with different AI models directly from your command line
- Process and analyze files using AI
- Incorporate AI-generated responses into your workflow

Whether you're a developer, researcher, or anyone looking to leverage AI in their daily tasks, Hermes provides an easy-to-use interface to harness the power of various AI models.

## Installation

Follow these steps to install Hermes:

1. Open your terminal or command prompt.

2. Clone the Hermes repository:
   ```
   git clone https://github.com/KoStard/HermesCLI
   ```

3. Navigate to the Hermes directory:
   ```
   cd HermesCLI
   ```

4. Install Hermes in editable mode:
   ```
   pip install -e .
   ```

## Configuration

After installation, you need to set up your configuration file. This file will store your API keys and default settings.

1. Create a configuration directory:
   - On macOS and Linux:
     ```
     mkdir -p ~/.config/hermes
     ```
   - On Windows:
     ```
     mkdir %USERPROFILE%\.config\hermes
     ```

2. Create a configuration file named `config.ini` in the directory you just created:
   - On macOS and Linux:
     ```
     touch ~/.config/hermes/config.ini
     ```
   - On Windows:
     ```
     type nul > %USERPROFILE%\.config\hermes\config.ini
     ```

3. Open the `config.ini` file in a text editor and add your configuration:

   ```ini
   [BASE]
   model = claude

   [ANTHROPIC]
   api_key = your_anthropic_api_key

   [GEMINI]
   api_key = your_gemini_api_key

   [OPENAI]
   api_key = your_openai_api_key

   [DEEPSEEK]
   api_key = your_deepseek_api_key
   model = deepseek-coder
   ```

   Replace `your_*_api_key` with your actual API keys.

### What are API Keys?

API keys are unique identifiers that authenticate your requests to AI services. They are like passwords that allow you to access and use these services. Each AI provider (like Anthropic, Google, OpenAI) has its own method for generating and managing API keys.

### How to Get API Keys

1. **Anthropic (Claude)**:
   - Visit [Anthropic's website](https://www.anthropic.com)
   - Sign up for an account
   - Navigate to the API section to generate your key

2. **Google (Gemini)**:
   - Go to the [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create or sign in to your Google account
   - Follow the prompts to create an API key

3. **OpenAI**:
   - Visit [OpenAI's website](https://openai.com)
   - Create an account or log in
   - Go to the API section and generate a new API key

4. **DeepSeek**:
   - Sign up at [DeepSeek AI](https://platform.deepseek.com/)
   - Navigate to your account settings or API section
   - Generate a new API key

Remember to keep your API keys secure and never share them publicly.

## Basic Usage

Here's how to use Hermes:

1. Open your terminal or command prompt.

2. To start a conversation with the default AI model:
   ```
   hermes
   ```

3. To use a specific model and include files for context:
   ```
   hermes --model claude document1.txt document2.txt
   ```

4. After running the command, you'll be prompted to enter your message or question.

## Command-line Options

Hermes supports various command-line options:

- `--model`: Specify the AI model to use (e.g., claude, gemini, openai)
- `--prompt`: Provide an initial prompt directly
- `--prompt-file`: Use a file containing the initial prompt
- `--append` or `-a`: Append the AI's response to a specified file
- `--update` or `-u`: Update a specified file with the AI's response
- `--pretty`: Display the output with markdown formatting
- `--image`: Include an image file in the context (can be used multiple times)
- `--text`: Add extra text to the context (can be used multiple times)
- `--url`: Include content from a URL in the context (can be used multiple times)

## Examples

1. Summarize a document:
   ```
   hermes --model claude README.md --prompt "Summarize this document in one paragraph"
   ```

2. Ask a question and save the response:
   ```
   hermes --prompt "What is the capital of France?" --append answer.txt
   ```

3. Use an image in your query:
   ```
   hermes --model gemini --image photo.jpg --prompt "Describe this image"
   ```

4. Pipe input and output:
   ```
   echo "Tell me a fun fact" | hermes > fun_fact.txt
   ```

## Supported Models

Hermes supports a variety of AI models:

- Claude (Anthropic)
- Gemini (Google)
- GPT-4 (OpenAI)
- Bedrock models (AWS)
- Ollama (for local models)
- DeepSeek
- And more...

Each model may have specific setup requirements. Refer to the documentation of each AI provider for detailed instructions on how to use their models.

## Contributing

We welcome contributions to Hermes! If you have ideas for improvements or have found a bug, please feel free to:

- Submit pull requests
- Create issues
- Suggest new features

Your input helps make Hermes better for everyone.

## License

Hermes is licensed under the Apache License 2.0. For full details, see the [LICENSE](LICENSE) file in the project repository.
