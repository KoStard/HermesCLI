# Hermes Workflow Specification

## Overview

Hermes workflows are defined using YAML files. These files describe a series of tasks to be executed sequentially or conditionally, allowing for complex interactions between AI models, shell commands, and file operations.

## Root Structure

The root of the workflow YAML file should contain a single key-value pair, where the key is the ID of the root task, and the value is the task configuration.

Example:

```yaml
my_root_task:
  type: sequential
  tasks:
    # ... task definitions ...
```

## Task Types

### Common Task Properties

All tasks have the following common properties:

- `type`: (Required) The type of the task (e.g., "sequential", "llm", "shell", etc.)
- `print_output`: (Optional) Boolean flag to indicate whether the task's output should be printed (default: false)

### Sequential Task

A sequential task executes a series of subtasks in order.

Properties:
- `type`: "sequential"
- `tasks`: A list of subtasks to execute

Example:

```yaml
my_sequential_task:
  type: sequential
  tasks:
    - task1:
        # ... task1 configuration ...
    - task2:
        # ... task2 configuration ...
```

### LLM Task

An LLM task sends a prompt to an AI model and processes the response.

Properties:
- `type`: "llm"
- `prompt`: The prompt to send to the AI model
- `pass_input_files`: (Optional) Boolean flag to indicate whether to pass input files to the model (default: false)
- `output_mapping`: (Optional) A dictionary mapping output keys to result properties

Example:

```yaml
llm_task:
  type: llm
  prompt: "Summarize the following text: {input_text}"
  pass_input_files: true
  output_mapping:
    summary: result.response
```

### Shell Task

A shell task executes a shell command.

Properties:
- `type`: "shell"
- `command`: The shell command to execute

Example:

```yaml
shell_task:
  type: shell
  command: "echo 'Hello, World!' > output.txt"
```

### Markdown Extraction Task

A markdown extraction task processes a single PDF file and extracts its content as markdown.

Properties:
- `type`: "markdown_extract"
- `file_path_var`: (Optional) The name of the global context variable containing the file path (default: "file_path")

Example:

```yaml
extract_task:
  type: markdown_extract
  file_path_var: input_file
```

To process multiple PDF files, you can use the `MapTask` in combination with the `MarkdownExtractionTask`:

```yaml
process_pdfs:
  type: map
  iterable: pdf_files
  task:
    type: markdown_extract
    file_path_var: item
    output_mapping:
      extracted_texts: result.extracted_text
```

In this example, `pdf_files` should be a list of file paths in the global context.

### Map Task

A map task applies a subtask to each item in an iterable.

Properties:
- `type`: "map"
- `iterable`: The name of the global context variable containing the iterable
- `task`: The subtask configuration to apply to each item

Example:

```yaml
map_task:
  type: map
  iterable: my_list
  task:
    type: llm
    prompt: "Process this item: {item}"
```

### If-Else Task

An if-else task conditionally executes one of two subtasks based on a condition.

Properties:
- `type`: "if_else"
- `condition`: A Python expression to evaluate
- `if_task`: The task to execute if the condition is true
- `else_task`: (Optional) The task to execute if the condition is false

Example:

```yaml
conditional_task:
  type: if_else
  condition: "len(summary) > 100"
  if_task:
    type: llm
    prompt: "The summary is long. Please shorten it."
  else_task:
    type: llm
    prompt: "The summary is concise. Please elaborate on it."
```

## Context and Variable Passing

- Global context variables can be accessed using curly braces `{}` in prompts and commands.
- Tasks can update the global context using the `output_mapping` property.
- The `item` variable is available in map task subtasks.

## Best Practices

1. Use descriptive task IDs to make your workflow more readable.
2. Leverage sequential tasks to group related operations.
3. Use output mappings to pass data between tasks effectively.
4. Take advantage of conditional tasks to create dynamic workflows.
5. Use map tasks for batch processing of data.

## Example Workflow

Here's an example of a more complex workflow that demonstrates various task types and their interactions:

```yaml
process_documents:
  type: sequential
  tasks:
    - extract_content:
        type: markdown_extract

    - summarize_documents:
        type: map
        iterable: input_files
        task:
          type: llm
          prompt: "Summarize the following document: {item}"
          output_mapping:
            summaries: result.response

    - combine_summaries:
        type: llm
        prompt: "Combine the following summaries into a single coherent summary: {summaries}"
        output_mapping:
          final_summary: result.response

    - save_summary:
        type: shell
        command: "echo '{final_summary}' > final_summary.txt"

    - generate_questions:
        type: if_else
        condition: "len(final_summary) > 500"
        if_task:
          type: llm
          prompt: "Generate 5 in-depth questions based on this long summary: {final_summary}"
        else_task:
          type: llm
          prompt: "Generate 3 basic questions based on this short summary: {final_summary}"
        output_mapping:
          questions: result.response

    - save_questions:
        type: shell
        command: "echo '{questions}' >> final_summary.txt"
```

This workflow extracts content from input files, summarizes each document, combines the summaries, saves the result, and generates questions based on the summary length.
