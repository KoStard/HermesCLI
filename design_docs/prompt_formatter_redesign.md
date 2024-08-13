# Prompt Formatter Redesign

## Overview
This document outlines a redesign of the prompt formatting system to better support different models within the Bedrock framework, with a primary focus on Claude while maintaining flexibility for other models.

## Key Concepts
1. Composable Formatters: Create a system where model-specific formatters can be composed with the Bedrock formatter.
2. XML-First Approach: Prioritize XML formatting for Claude while supporting other formats.
3. File Operations as Native Features: Integrate file operations (read, update, append) as native features in the prompt structure.
4. Flexible Response Parsing: Design a system to parse model responses that can handle different output formats.

## Proposed Architecture

### 1. Base Formatter
- Define an abstract base class `BaseFormatter` with common methods.

### 2. Model-Specific Formatters
- Create formatters for specific models (e.g., `ClaudeFormatter`, `MistralFormatter`).
- These formatters will handle model-specific prompt structures.

### 3. Bedrock Formatter
- Create a `BedrockFormatter` that wraps model-specific formatters.
- This formatter will handle the Bedrock Converse API structure.

### 4. Formatter Factory
- Implement a factory class to create the appropriate formatter based on the model.

### 5. File Operation Integration
- Include file operation capabilities in the prompt structure.
- Design a consistent way to represent file operations across different formats.

## Prompt Structure Examples

### Claude (XML) within Bedrock
```python
[
    {'text': '''
    <input>
      <system_message>You are an AI assistant with file operation capabilities.</system_message>
      <files>
        <file name="example.txt" permissions="read,write,append">
          File content here...
        </file>
      </files>
      <user_message>User's prompt here...</user_message>
    </input>
    '''}
]
```

### Other Model (e.g., JSON) within Bedrock
```python
[
    {'text': '''
    {
      "system_message": "You are an AI assistant with file operation capabilities.",
      "files": [
        {
          "name": "example.txt",
          "permissions": ["read", "write", "append"],
          "content": "File content here..."
        }
      ],
      "user_message": "User's prompt here..."
    }
    '''}
]
```

## Implementation Steps
1. Create the `BaseFormatter` abstract class.
2. Implement model-specific formatters (starting with `ClaudeFormatter`).
3. Develop the `BedrockFormatter` to wrap model-specific formatters.
4. Create a `FormatterFactory` to instantiate the appropriate formatter.
5. Update `ChatApplication` to use the new formatter system.
6. Modify file processors to work with the new prompt structure.
7. Update main script to use the new formatter system.

## Benefits
- Better support for Claude within Bedrock.
- Flexibility to add support for other models easily.
- Cleaner separation of concerns between Bedrock API requirements and model-specific formatting.
- Improved integration of file operations into the prompt structure.

## Next Steps
1. Review and refine this high-level design.
2. Create detailed specifications for each component.
3. Implement the base classes and Claude-specific formatter.
4. Gradually extend to other models as needed.
