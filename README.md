# Hermes: Chat with AI Models, Files, and Execute Workflows

Hermes is a powerful command-line tool that enables you to interact with various AI models, process files, and execute complex workflows. Named after the messenger god in Greek mythology, Hermes facilitates seamless communication between you, AI models, and your local files.

## What Hermes Can Do

- Chat with a variety of AI models:
  - Claude (Anthropic)
  - Bedrock Claude 3.5
  - Gemini (Google)
  - GPT-4 (OpenAI)
  - Ollama (Local models)
  - DeepSeek (DeepSeek AI)
  - And many more...
- File input support for context-aware conversations
- Image inputs for supported models
- URL input to read and pass to the LLM
- Support for local models through Ollama integration
- Ability to append or update files based on AI responses
- Markdown rendering for formatted output
- Execute complex workflows defined in YAML files
- Extension model to support custom context providers (e.g. custom parsers for different file formats, web pages, etc.)
- Pipe the input into the LLM
- Pipe the output from the LLM

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/KoStard/HermesCLI
   cd HermesCLI
   ```

2. Install the package in editable mode:
   ```
   pip install -e .
   ```

After installation, set up your configuration file:

1. Create a file named `config.ini` in the following location:
   - On Unix-like systems (Linux, macOS): `~/.config/hermes/config.ini`
   - On Windows: `C:\Users\YourUsername\.config\hermes\config.ini`

2. Add your API keys and default model to the config file:
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
   
   You can set any supported model as the default in the `[BASE]` section.

   Note: The application will create the necessary directories if they don't exist.


## Usage
### Basic usage

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

- `--model`: Specify the AI model to use (e.g., claude, bedrock-claude, gemini, openai, ollama, deepseek)
- `--prompt`: Specify the initial prompt directly from the command line
- `--prompt-file`: Specify a file containing the initial prompt
- `--append` or `-a`: Append the AI's response to a specified file
- `--update` or `-u`: Update a specified file with the AI's response
- `--pretty`: Print the output by rendering markdown
- `--workflow`: Specify a workflow YAML file to execute
- `--image`: Pass an image to the LLM (can be used multiple times)
- `--text`: Additional text to be included with prompts (can be used multiple times)
- `--url`: Pass a URL, that will be opened, parsed and passed to the LLM  (can be used multiple times)

If you pipe into the input of hermes, or pipe the output of hermes, it will call the LLM only once, print the output and exit.

You can also implement your own custom context providers, which will be accessible from CLI with your own custom arguments.
#### Configuring custom context providers
Create a sub-folder in `~/.config/hermes/extra_context_providers/`, you can name it something about the group of extensions you are adding, or just call it `extensions`.
Then inside `~/.config/hermes/extra_context_providers/<your_extensions_folder>/` create a python file (use snake_case for the name of the file).
There create a class, that implements `hermes.context_providers.base.ContextProvider`.

Example:
```python
# /home/kostard/.config/hermes/extra_context_providers/my_test/test.py

from argparse import ArgumentParser
from hermes.context_providers.base import ContextProvider
from hermes.config import HermesConfig
from hermes.prompt_builders.base import PromptBuilder

class TestContextProvider(ContextProvider):
    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument('--test', help="My test context provider")

    def load_context(self, config: HermesConfig):
	    # HermesConfig contains all the arguments parsed from CLI, so the --test is present here
        # This is my opportunity to load and store some context. If I need to make network requests, I can do it here.
        self.test = config.get('test', 'default_test')

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        # This is my opportunity to add something to the prompt
        prompt_builder.add_text(self.test, name="test")

```
Now we'll see:
```sh
hermes --help
# ...
#   --test TEST           My test context provider

hermes --test "My secret is 1234" --prompt "what is my secret?"
# Your secret is "1234".
```
#### Examples:

Summarise a document, and continue chatting about it:
```sh
hermes --model claude README.md --prompt "Summarise this document into 1 paragraph"
# Hermes is a versatile command-line tool that enables users to interact with various AI models, process files, and execute complex workflows. It supports a wide range of AI models, including Claude, GPT-4, Gemini, and local models through Ollama integration. Hermes offers features such as file and image input support, URL parsing, the ability to append or update files based on AI responses, markdown rendering, and the execution of workflows defined in YAML files. Users can easily install Hermes, configure API keys, and use it with various command-line options to chat with AI models, process documents, and run complex tasks. The tool also supports piping input and output, making it a powerful and flexible solution for AI-assisted tasks and automation.
# ----
# You:
```

Piping the output:
```sh
hermes --prompt "Tell me a fact about space for my curiosity" | cat
# Sure! Here's a fascinating fact about space:
# 
# The Sun, which is the center of our solar system, is made up of about 98% hydrogen and helium. It has a diameter of approximately 1.39 million kilometers (864,000 miles), which is about 109 times the diameter of Earth. Despite its immense size, the Sun is considered an average-sized star in the vastness of the universe.
```

Piping input:
```sh
echo "Hello, how are you?" | hermes
# Hello! I'm here to help. How can I assist you today?
```

Using --workflow:
```
hermes --workflow my_workflow.yaml --model claude
```

### Supported Models

- `claude`: Anthropic's Claude model
- `bedrock/sonnet-3`: AWS Bedrock Claude Sonnet 3 model
- `bedrock/sonnet-3.5`: AWS Bedrock Claude Sonnet 3.5 model
- `bedrock/opus-3`: AWS Bedrock Claude 3 Opus model
- `bedrock/mistral`: AWS Bedrock Mistral model
- `gemini`: Google's Gemini model
- `openai`: OpenAI's GPT-4 model
- `ollama`: Local models through Ollama
- `deepseek`: DeepSeek AI's models
- `groq`: You specify which groq model in the config file

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
3. In your `~/.config/hermes/config.ini`, add:
   ```ini
   [OLLAMA]
   model = llama2
```
   Replace `llama2` with your preferred model.

### DeepSeek Setup

To use DeepSeek models:

1. Sign up for an account at [DeepSeek AI](https://platform.deepseek.com/)
2. Obtain your API key from the DeepSeek platform
3. For DeepSeek models, add the following to your `~/.config/hermes/config.ini`:
   ```ini
   [DEEPSEEK]
   api_key = your_deepseek_api_key
   base_url = https://api.deepseek.com
   model = deepseek-coder
   ```
   You can replace `deepseek-coder` with other available DeepSeek models if desired.

## Contributing

Contributions to Hermes are welcome! Please feel free to submit pull requests, create issues, or suggest new features.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Using Workflows

Hermes now supports executing complex workflows defined in YAML files. Here's a simple example of how to use workflows:

1. Create a YAML file defining your workflow (e.g., `my_workflow.yaml`):

```yaml
my_root_task:
  type: sequential
  tasks:
    task1:
      type: llm
      prompt: "Hello, world!"
    task2:
      type: shell
      command: "echo 'Task completed'"
```

2. Run the workflow using the Hermes CLI:

```
hermes --workflow my_workflow.yaml --model claude
```

This workflow does the following:
1. Sends a prompt to the LLM to summarize some input text.
2. Saves the summary to a file using a shell command.
3. Generates questions based on the summary using the LLM.

You can define more complex workflows with multiple LLM and shell tasks, using the output of one task as input for another. The new structure allows for nesting sequential tasks, providing more flexibility in workflow design.

Example of a nested sequential task:

```yaml
type: sequential
tasks:
  - id: task1
    type: llm
    prompt: "Summarize the following text: {input_text}"
    output_mapping:
      summary: result.response

  - id: nested_tasks
    type: sequential
    tasks:
      - id: subtask1
        type: shell
        command: "echo 'Summary: {summary}' > summary.txt"

      - id: subtask2
        type: llm
        prompt: "Generate 3 questions based on this summary: {summary}"
        output_mapping:
          questions: result.response

  - id: task3
    type: shell
    command: "echo 'Questions: {questions}' >> summary.txt"
```

This structure allows for more complex and organized workflows, with the ability to group related tasks together using nested sequential tasks.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
