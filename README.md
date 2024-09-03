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
  - DeepSeek (DeepSeek AI)
- File input support for context-aware conversations
- Image inputs for supported models
- Support for local models through Ollama integration
- Ability to append or update files based on AI responses
- Markdown rendering for formatted output
- Raw output option for unformatted responses
- Confirmation prompt to prevent unnecessary API calls
- Autocomplete support for model selection
- **NEW: Execute complex workflows defined in YAML files**
- **NEW: Context extension feature for dynamic file inclusion in workflows**

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/KoStard/HermesCLI
   cd HermesCLI
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your configuration file:
   Create a file named `config.ini` in the following location:
   - On Unix-like systems (Linux, macOS): `~/.config/multillmchat/config.ini`
   - On Windows: `C:\Users\YourUsername\.config\multillmchat\config.ini`

   Add your API keys and default model to the config file:
   ```ini
   [DEFAULT]
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
   
   You can set any supported model as the default in the `[DEFAULT]` section.

   Note: The application will create the necessary directories if they don't exist.

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

- `--model`: Specify the AI model to use (e.g., claude, bedrock-claude, gemini, openai, ollama, deepseek)
- `--prompt`: Specify the initial prompt directly from the command line
- `--prompt-file`: Specify a file containing the initial prompt
- `--append` or `-a`: Append the AI's response to a specified file
- `--update` or `-u`: Update a specified file with the AI's response
- `--pretty`: Print the output by rendering markdown (default behavior)
- `--workflow`: Specify a workflow YAML file to execute
- `--text`: Additional text to be included with prompts (can be used multiple times)

Examples:

Using --prompt:
```
hermes --model claude document1.txt document2.txt --prompt "Summarize these documents."
```

Using --prompt-file:
```
hermes --model claude document1.txt document2.txt --prompt-file my_prompt.txt
```

Using --workflow:
```
hermes --workflow my_workflow.yaml --model claude
```

Using --text:
```
hermes --model claude document1.txt --text "Consider this context" --text "And this additional information"
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
- `deepseek`: DeepSeek AI's models

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

### DeepSeek Setup

To use DeepSeek models:

1. Sign up for an account at [DeepSeek AI](https://platform.deepseek.com/)
2. Obtain your API key from the DeepSeek platform
3. In your `~/.config/multillmchat/config.ini`, add:
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

## NEW: Context Extension Feature

Hermes now supports dynamic file inclusion in workflows using the context extension feature. This allows you to add files to the context during workflow execution, making your workflows more flexible and powerful.

To use the context extension feature, you can include a `context_extension` task in your workflow YAML file. Here's an example:

```yaml
my_workflow:
  type: sequential
  tasks:
    task1:
      type: context_extension
      files:
        - additional_file1.txt
        - additional_file2.txt

    task2:
      type: llm
      prompt: "Analyze the content of all files in the context."
      pass_input_files: true
```

In this example:

1. The `context_extension` task adds `additional_file1.txt` and `additional_file2.txt` to the context.
2. The subsequent `llm` task can now access these additional files along with any files initially provided when running the Hermes command.

The `pass_input_files: true` option in the LLM task ensures that all files in the context (including the newly added ones) are passed to the AI model for analysis.

This feature is particularly useful when you need to include different sets of files for different parts of your workflow, or when you want to dynamically add files based on the results of previous tasks.

Remember to ensure that the files specified in the `context_extension` task exist in the directory where you're running the Hermes command, or provide the full path to these files.
