# Design Document: Enhancing Configuration Handling in Hermes

## Table of Contents
1. [Introduction](#introduction)
2. [Background](#background)
3. [Problem Statement](#problem-statement)
4. [Current Architecture Analysis](#current-architecture-analysis)
    - [Configuration Flow](#configuration-flow)
    - [Issues Identified](#issues-identified)
    - [Codebase Overview](#codebase-overview)
5. [Proposed Solutions](#proposed-solutions)
    - [Solution 1: Separate Global and Provider Configurations](#solution-1-separate-global-and-provider-configurations)
    - [Solution 2: Modular Argument Parsing with Subparsers](#solution-2-modular-argument-parsing-with-subparsers)
    - [Solution 3: Utilize Configuration Management Libraries](#solution-3-utilize-configuration-management-libraries)
6. [Comparison of Solutions](#comparison-of-solutions)
7. [Recommended Approach](#recommended-approach)
    - [Implementation Details](#implementation-details)
    - [Code Examples](#code-examples)
    - [ASCII Diagram: Proposed Configuration Flow](#ascii-diagram-proposed-configuration-flow)
8. [User Experience Considerations](#user-experience-considerations)
9. [Conclusion](#conclusion)

## Introduction

This document outlines an improved architecture for handling configurations within the Hermes codebase. Specifically, it addresses the current challenges associated with the `HermesConfig` class, which conflates global CLI arguments with context provider-specific arguments. The goal is to establish a clear, maintainable, and scalable configuration management system that enhances code clarity and user experience.

## Background

Hermes is a versatile multi-model chat application that relies on various context providers to enrich user interactions. The application currently employs the `HermesConfig` class to manage all CLI arguments uniformly. While this approach simplifies integration by treating all arguments consistently, it leads to confusion and maintainability issues, especially as the number of context providers grows.

## Problem Statement

The existing implementation of `HermesConfig` suffers from the following issues:

- **Mixed Concerns**: Global CLI arguments (e.g., `--model`, `--pretty`) are handled alongside context provider-specific arguments (e.g., `--text`, `--image`) within the same configuration object.
  
- **Inadequate Data Structures**: The `get` method of `HermesConfig` returns lists for all arguments, which is inappropriate for singular arguments like `--model` and `--pretty`.

- **Scalability Challenges**: As more context providers are added, managing configurations becomes increasingly complex and error-prone.

- **User Confusion**: Users may find it difficult to discern which arguments are global and which pertain to specific context providers, leading to misuse or misconfiguration.

## Current Architecture Analysis

### Configuration Flow

1. **Argument Parsing**: The `argparse` module is used in `src/hermes/main.py` to parse all CLI arguments. Context providers dynamically add their specific arguments via the `add_argument` method.
   
2. **HermesConfig Creation**: Parsed arguments are encapsulated within the `HermesConfig` class, which stores configurations as a dictionary mapping keys to lists of values.
   
3. **Context Providers Consumption**: Each context provider retrieves its specific configuration by accessing the `HermesConfig` instance using the `get` method.

### Issues Identified

- **Conflated Configurations**: Global and provider-specific arguments are intermixed within `HermesConfig`, lacking clear boundaries.

- **List-Based Retrieval**: The use of lists for all configuration values is unsuitable for arguments that are inherently singular, causing unnecessary complexity.

- **Maintenance Overhead**: Adding new context providers requires careful management to avoid configuration conflicts or ambiguities.

### Codebase Overview

Key components involved in configuration handling:

- **`src/hermes/main.py`**: Parses CLI arguments and initializes the application based on the configurations.

- **`src/hermes/config.py`**: Defines the `HermesConfig` class, which wraps parsed arguments.

- **Context Providers (`src/hermes/context_providers/`*)**: Each context provider defines its own arguments and interacts with `HermesConfig` to load configurations.

- **`src/hermes/context_provider_loader.py`**: Dynamically loads all context providers.

### Existing Configuration Example

```python
# src/hermes/config.py
class HermesConfig:
    def __init__(self, config: Dict[str, List[str]]):
        self._config = config

    def get(self, key: str, default=None) -> List[str] | None:
        return self._config.get(key, default)

    def set(self, key: str, value: str | List[str]):
        if type(value) is str:
            value = [value]
        self._config[key] = value
```

```python
# src/hermes/main.py
def main():
    parser = argparse.ArgumentParser(description="Multi-model chat application with workflow support")
    parser.add_argument("--model", choices=ModelRegistry.get_available_models(), help="Choose the model to use (optional if configured in config.ini)")
    parser.add_argument("--pretty", help="Print the output by rendering markdown", action="store_true")
    # Context providers add their own arguments
    for provider_class in context_provider_classes:
        provider_class.add_argument(parser)
    args = parser.parse_args()
    hermes_config = create_config_from_args(args)
    # Application logic follows...
```

## Proposed Solutions

### Solution 1: Separate Global and Provider Configurations

**Description**: Distinguish between global configurations and context provider-specific configurations by maintaining separate configuration layers or objects.

**Implementation Steps**:
- **GlobalConfig**: Capture arguments like `--model`, `--pretty`, etc., in a dedicated configuration object.
- **ProviderConfig**: Each context provider manages its own configuration independently.
- **Processing Flow**: Parse global arguments first, then delegate context provider argument parsing to respective modules.

**Pros**:
- Clear separation of concerns.
- Avoids mixing unrelated configurations.
- Enhances readability and maintainability.

**Cons**:
- Requires restructuring of the current configuration flow.
- Potential duplication of argument definitions if not managed carefully.

### Solution 2: Modular Argument Parsing with Subparsers

**Description**: Implement a modular approach to argument parsing where global and context provider-specific arguments are handled using `argparse` subparsers or distinct namespaces.

**Implementation Steps**:
- **Primary Parser**: Define global arguments (`--model`, `--pretty`, etc.) in the primary `ArgumentParser`.
- **Subparsers for Providers**: Utilize `argparse`'s subparsers to delegate provider-specific arguments to their respective subcommands.
- **Configuration Segregation**: Map configurations to their respective namespaces within `HermesConfig`.

**Pros**:
- Maintains modularity, allowing providers to be more self-contained.
- Reduces the risk of argument name collisions.
- Facilitates easier addition of new providers.

**Cons**:
- Increased complexity in managing multiple parsers or namespaces.
- May require significant changes to the existing parsing logic.

### Solution 3: Utilize Configuration Management Libraries

**Description**: Adopt dedicated configuration management libraries (e.g., `pydantic`, `dataclasses`) to define and manage configurations more effectively.

**Implementation Steps**:
- **Define Configuration Models**: Use data models to represent global and provider-specific configurations.
- **Validation and Parsing**: Leverage library features for validation, default values, and type enforcement.
- **Integration with `argparse`**: Map parsed CLI arguments to the respective configuration models.

**Pros**:
- Enhanced type safety and validation.
- Improved clarity through explicit configuration models.
- Potential for reusability and consistency across the codebase.

**Cons**:
- Learning curve associated with new libraries.
- Additional dependencies increase the project footprint.
- Requires comprehensive refactoring to integrate models.

## Comparison of Solutions

| Feature                        | Solution 1: Separate Configs | Solution 2: Subparsers        | Solution 3: Config Libraries   |
|--------------------------------|------------------------------|-------------------------------|--------------------------------|
| **Separation of Concerns**     | High                         | High                          | High                           |
| **Implementation Effort**      | Medium                       | High                          | High                           |
| **Scalability**                | Good                         | Excellent                     | Excellent                      |
| **Complexity**                 | Medium                       | High                          | Medium                         |
| **Validation Support**         | Low                          | Medium                        | High                           |
| **Dependency Addition**        | None                         | None                          | Yes                            |

## Recommended Approach

**Solution 2: Modular Argument Parsing with Subparsers** is recommended due to its scalability and clear separation of concerns. Although it introduces additional complexity, the benefits in maintaining a clean architecture and facilitating future expansions outweigh the drawbacks.

**Supplementary Recommendation**: Incorporate aspects of **Solution 3**, such as using configuration models for validation and type enforcement, to enhance robustness without fully adopting a new library.

### Implementation Details

1. **Refactor Argument Parsing**:
    - Initialize the primary `ArgumentParser` with global arguments.
    - Create subparsers for each context provider, allowing them to define their own arguments within their namespace.
  
2. **Update `HermesConfig`**:
    - Modify `HermesConfig` to handle separate namespaces for global and provider-specific configurations.
    - Implement getters that retrieve configurations from the appropriate namespace.

3. **Modify Context Providers**:
    - Adjust each context provider to register its arguments under its subparser.
    - Ensure that context providers retrieve their configurations from their dedicated sections within `HermesConfig`.

4. **Testing & Validation**:
    - Develop comprehensive tests to ensure configurations are correctly parsed and segregated.
    - Validate that global and provider-specific arguments do not interfere with each other.

### Code Examples

**Refactored Argument Parsing in `main.py`**:

```python
# src/hermes/main.py
def main():
    parser = argparse.ArgumentParser(description="Multi-model chat application with workflow support")
    
    # Global arguments
    parser.add_argument("--model", choices=ModelRegistry.get_available_models(), help="Choose the model to use (optional if configured in config.ini)")
    parser.add_argument("--pretty", help="Print the output by rendering markdown", action="store_true")
    parser.add_argument("--workflow", help="Specify a workflow YAML file to execute")
    
    # Create subparsers for context providers
    subparsers = parser.add_subparsers(dest='provider', help='Context Provider Commands')
    
    # Load context providers dynamically
    context_provider_classes = load_context_providers()
    for provider_class in context_provider_classes:
        provider_parser = subparsers.add_parser(provider_class.__name__, help=f'{provider_class.__name__} context provider')
        provider_class.add_argument(provider_parser)
    
    args = parser.parse_args()
    
    setup_logger()
    
    hermes_config = create_config_from_args(args)
    
    if hermes_config.get('workflow'):
        run_workflow(hermes_config)
    else:
        run_chat_application(hermes_config, context_provider_classes)
```

**Updated `HermesConfig` Handling**:

```python
# src/hermes/config.py
from typing import Dict, Any, List

class HermesConfig:
    def __init__(self, global_config: Dict[str, Any], provider_configs: Dict[str, Dict[str, Any]]):
        self.global_config = global_config
        self.provider_configs = provider_configs

    def get_global(self, key: str, default=None) -> Any:
        return self.global_config.get(key, default)

    def get_provider_config(self, provider: str, key: str, default=None) -> Any:
        return self.provider_configs.get(provider, {}).get(key, default)

def create_config_from_args(args) -> HermesConfig:
    global_config = {}
    provider_configs = {}
    
    # Extract global arguments
    global_keys = ['model', 'pretty', 'workflow']
    for key in global_keys:
        value = getattr(args, key, None)
        if value is not None:
            global_config[key] = value
    
    # Extract provider-specific arguments
    provider = getattr(args, 'provider', None)
    if provider:
        provider_config = {}
        provider_class = next((cls for cls in load_context_providers() if cls.__name__ == provider), None)
        if provider_class:
            for action in provider_class.add_argument.__func__.__code__.co_varnames:
                value = getattr(args, action, None)
                if value is not None:
                    provider_config[action] = value
            provider_configs[provider] = provider_config
    
    return HermesConfig(global_config, provider_configs)
```

**Context Provider Argument Registration**:

```python
# Example: src/hermes/context_providers/text_context_provider.py
class TextContextProvider(ContextProvider):
    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument('--text', type=str, action='append', help='Text to be included in the context (can be used multiple times)')
```

### ASCII Diagram: Proposed Configuration Flow

```
+-------------------+
|    Command Line   |
|     Arguments     |
+---------+---------+
          |
          v
+-------------------+
|     argparse      |
| (Global Parser)   |
+---------+---------+
          |
          v
+-------------------+
| GlobalConfig      |
| (model, pretty,   |
|  workflow, etc.)  |
+---------+---------+
          |
          v
+-------------------+
|     Subparsers    |
| (One per Context  |
|   Provider)       |
+---------+---------+
          |
          v
+-------------------+          +-------------------------+
| ProviderConfig    |          | ProviderContextProvider |
| (Provider-specific|          | (e.g., TextContextProv.)|
|  Arguments)       |          +-------------------------+
+-------------------+
```

## User Experience Considerations

- **Consistency**: Users can clearly distinguish between global and context-specific arguments, reducing confusion.
  
- **Ease of Use**: Providing subcommands for context providers allows users to interact with specific providers without worrying about argument collisions.
  
- **Scalability**: Adding new context providers becomes straightforward, as each can define its own arguments within its namespace.

- **Error Handling**: Enhanced separation allows for more precise error messages related to configuration issues.

## Conclusion

The current configuration handling in Hermes merges global and context provider-specific arguments within a single `HermesConfig` class, leading to confusion and maintainability challenges. By adopting a modular argument parsing approach using `argparse` subparsers, we can achieve a clear separation of concerns, enhance scalability, and improve user experience. This restructuring, complemented by structured configuration management practices, will position Hermes for robust growth and ease of maintenance.

