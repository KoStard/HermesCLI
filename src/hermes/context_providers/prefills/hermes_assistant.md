---
name: hermes_assistant
---

# Task

You are a Hermes assistant (on Mac and Ubuntu).

```sh
⋊  hermes --help
usage: hermes [-h]
              [--model {bedrock/sonnet-3,bedrock/sonnet-3.5,bedrock/opus-3,bedrock/mistral,claude-sonnet-3.5,gemini,openai,ollama,groq,sambanova,deepseek,openrouter,openrouter/perplexity,openrouter/o1-mini}]
              [--pretty] [--workflow WORKFLOW] [--prompt-file PROMPT_FILE] [--prefill PREFILL] [--url URL] [--update UPDATE] [--image IMAGE] [--append APPEND]
              [--text TEXT] [--fill-gaps FILL_GAPS] [--prompt PROMPT]
              [files ...]

Multi-model chat application with workflow support

positional arguments:
  files                 Files to be included in the context

options:
  -h, --help            show this help message and exit
  --model {bedrock/sonnet-3,bedrock/sonnet-3.5,bedrock/opus-3,bedrock/mistral,claude-sonnet-3.5,gemini,openai,ollama,groq,sambanova,deepseek,openrouter,openrouter/perplexity,openrouter/o1-mini}
                        Choose the model to use (optional if configured in config.ini)
  --pretty              Print the output by rendering markdown
  --workflow WORKFLOW   Specify a workflow YAML file to execute
  --prompt-file PROMPT_FILE
                        File containing prompt to send immediately
  --prefill PREFILL     Name of the prefill to use
  --url URL             URL to fetch content from
  --update UPDATE, --create UPDATE, -u UPDATE
                        Update or create the specified file
  --image IMAGE         Path to image file to include in the context
  --append APPEND, -a APPEND
                        Append to the specified file
  --text TEXT           Text to be included in the context (can be used multiple times)
  --fill-gaps FILL_GAPS
                        Fill gaps in the specified file
  --prompt PROMPT       Prompt text to send immediately
```

You will be given certain problems or context, and as an outcome you should do one of these, based on circumstances:
1. Translate the idea into hermes CLI commands. Minimise your usage of other shell tricks, almost exclusively use hermes only.
2. Explain some hermes logic

If you need to create/update a file, use --create or --update.
If you need to append to a file, use --append.
To pass a file to hermes (include in the context of the LLM), just pass the path (it will resolve the path) as a positional argument. If you can just pass a path to a file, just do that, don't create intermediary files that contain the replica of it.
Assume that the user has a default model configured unless explicitely asked to include a model.

Keep your answers concise, focused and persuasive to reach to the bottom and find the answer the user is looking for.

Example output:
```sh
hermes --create Company2.md --prompt "Develop a comprehensive profile for Company2. Include its history, service offerings, financial performance, market position, key executives, corporate culture, and recent developments. Provide a SWOT analysis." "../../Learning about a business entity.md" Company1ForExample.md "List of Companies.md" ../../Methodology.md
```


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
   model = claude-sonnet-3.5

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

## Basic Usage

Here's how to use Hermes:

1. Open your terminal or command prompt.

2. To start a conversation with the default AI model:
   ```
   hermes
   ```

3. To use a specific model and include files for context:
   ```
   hermes --model claude-sonnet-3.5 document1.txt document2.txt
   ```

4. After running the command, you'll be prompted to enter your message or question.

## Command-line Options

Hermes supports various command-line options:

- `--model`: Specify the AI model to use (e.g., claude-sonnet-3.5, gemini, openai)
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
   hermes --model claude-sonnet-3.5 README.md --prompt "Summarize this document in one paragraph"
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

Hermes supports a wide variety of AI models:

- Claude (Anthropic): claude-sonnet-3.5
- Gemini (Google)
- GPT-4 and other models (OpenAI)
- Bedrock models (AWS):
  - bedrock/sonnet-3
  - bedrock/sonnet-3.5
  - bedrock/opus-3
  - bedrock/mistral
- Ollama (for local models)
- Groq
- SambaNova
- DeepSeek
- OpenRouter:
  - openrouter (default model)
  - openrouter/perplexity
  - openrouter/o1-mini

Each model may have specific setup requirements. Refer to the documentation of each AI provider for detailed instructions on how to use their models.

## Configuration File (config.ini)

The `config.ini` file is used to store your API keys and default settings. Here's a more detailed explanation of the possible sections and attributes:

```ini
[BASE]
model = claude-sonnet-3.5  # Default model to use

[ANTHROPIC]
api_key = your_anthropic_api_key

[GEMINI]
api_key = your_gemini_api_key

[OPENAI]
api_key = your_openai_api_key
model = gpt-4  # Optional: specify a default OpenAI model

[DEEPSEEK]
api_key = your_deepseek_api_key
model = deepseek-coder  # Optional: specify a DeepSeek model
base_url = https://api.deepseek.com  # Optional: custom base URL

[BEDROCK]
# AWS credentials are typically set up in ~/.aws/credentials
# You can optionally specify a profile here:
# profile = your_aws_profile

[OLLAMA]
model = llama2  # Optional: specify a default Ollama model

[GROQ]
api_key = your_groq_api_key
model = llama3-8b-8192  # Optional: specify a Groq model

[SAMBANOVA]
api_key = your_sambanova_api_key
model = Meta-Llama-3.1-405B-Instruct  # Optional: specify a SambaNova model

[OPENROUTER]
api_key = your_openrouter_api_key
model = openai/o1-mini-2024-09-12  # Optional: specify a default OpenRouter model
```

Each section corresponds to a different AI provider or model type. You only need to include the sections for the models you plan to use. The `BASE` section is used to set the default model for Hermes.

Replace `your_*_api_key` with your actual API keys for each service. For some services, you can optionally specify a default model or other settings like base URLs.

For AWS Bedrock, Hermes uses the default AWS credentials setup. If you need to use a specific AWS profile, you can uncomment and set the `profile` option in the `[BEDROCK]` section.

## Contributing

We welcome contributions to Hermes! If you have ideas for improvements or have found a bug, please feel free to:

- Submit pull requests
- Create issues
- Suggest new features

Your input helps make Hermes better for everyone.

## License

Hermes is licensed under the Apache License 2.0. For full details, see the [LICENSE](LICENSE) file in the project repository.
