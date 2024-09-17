# Design Document: Improving Configuration Handling in Hermes

## Table of Contents
1. [Introduction](#introduction)
2. [Background](#background)
3. [Problem Statement](#problem-statement)
4. [Current Architecture Analysis](#current-architecture-analysis)
5. [Proposed Solutions](#proposed-solutions)
    - [Solution 1: Separate Configuration Layers](#solution-1-separate-configuration-layers)
    - [Solution 2: Modular Argument Parsing](#solution-2-modular-argument-parsing)
    - [Solution 3: Utilize Configuration Management Libraries](#solution-3-utilize-configuration-management-libraries)
6. [Comparison of Solutions](#comparison-of-solutions)
7. [Recommended Approach](#recommended-approach)
8. [Implementation Plan](#implementation-plan)
9. [Conclusion](#conclusion)

## Introduction

This design document addresses the current challenges in handling configuration within the Hermes codebase, specifically focusing on the creation and usage of `HermesConfig`. The goal is to propose an improved architecture that distinguishes between global CLI arguments and context provider-specific arguments, enhancing code clarity and maintainability.

## Background

Hermes is a multi-model chat application that leverages various context providers to enrich interactions. The application currently uses `HermesConfig` to manage all CLI arguments uniformly. While this approach simplifies the integration of context providers by treating all arguments consistently, it inadvertently mixes global and provider-specific configurations, leading to confusion and potential maintenance issues.

## Problem Statement

The existing implementation of `HermesConfig` conflates global CLI arguments (e.g., `--model`, `--pretty`) with context provider-specific arguments (e.g., `--text`, `--image`). This amalgamation results in:
- **Confusion**: Users and developers struggle to differentiate between global settings and context-specific options.
- **Inconsistency**: Methods retrieving configuration values return lists, which may not be semantically appropriate for all arguments.
- **Maintainability**: As the number of context providers grows, managing configurations becomes increasingly complex and error-prone.

## Current Architecture Analysis

### Configuration Flow

1. **Argument Parsing**: `argparse` parses all CLI arguments, adding arguments from both global settings and context providers.
2. **HermesConfig Creation**: The parsed arguments are converted into a `HermesConfig` object, where each key maps to a list of values.
3. **Context Providers Consumption**: Context providers retrieve their specific configurations from `HermesConfig` using the `get` method.

### Issues Identified

- **Mixed Concerns**: `HermesConfig` handles both global and context-specific arguments without clear separation.
- **Data Structure Misalignment**: Storing all configuration values as lists is unsuitable for arguments that are inherently singular, such as `--model` and `--pretty`.
- **Scalability Constraints**: The current approach does not scale well with the addition of new context providers, as the configuration handling becomes more tangled.

### ASCII Diagram: Current Configuration Flow

```
+-------------------+
|    Command Line   |
|     Arguments     |
+---------+---------+
          |
          v
+-------------------+
|     argparse      |
|  (Parses all args)|
+---------+---------+
          |
          v
+-------------------+
|   HermesConfig    |
|  (Dict[str, List])|
+---------+---------+
          |
          v
+-------------------+
| Context Providers |
|  (Retrieve args)  |
+-------------------+
```

## Proposed Solutions

### Solution 1: Separate Configuration Layers

**Description**: Distinguish between global configurations and context provider configurations by maintaining separate configuration layers or objects.

**Implementation Steps**:
- **GlobalConfig**: Capture arguments like `--model`, `--pretty`, etc.
- **ProviderConfig**: Each context provider manages its own configuration independently.
- **Processing Flow**: Parse global arguments first, then delegate context provider argument parsing to respective modules.

**Pros**:
- Clear separation of concerns.
- Avoids mixing unrelated configurations.
- Enhances readability and maintainability.

**Cons**:
- Requires restructuring of the current configuration flow.
- Potential duplication of argument definitions if not managed carefully.

### Solution 2: Modular Argument Parsing

**Description**: Implement a modular approach to argument parsing where each context provider is responsible for registering and handling its own arguments.

**Implementation Steps**:
- **Provider Registration**: Each context provider registers its arguments with a dedicated parser or namespace.
- **Namespace Segregation**: Utilize `argparse`'s subparsers or distinct namespaces to segregate global and provider-specific arguments.
- **HermesConfig Refinement**: Refine `HermesConfig` to handle different namespaces appropriately.

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
- **Integration with argparse**: Map parsed CLI arguments to the respective configuration models.

**Pros**:
- Enhanced type safety and validation.
- Improved clarity through explicit configuration models.
- Potential for reusability and consistency across the codebase.

**Cons**:
- Learning curve associated with new libraries.
- Additional dependencies increase the project footprint.
- Requires comprehensive refactoring to integrate models.

## Comparison of Solutions

| Feature                        | Solution 1: Separate Layers | Solution 2: Modular Parsing | Solution 3: Config Libraries |
|--------------------------------|-----------------------------|------------------------------|-------------------------------|
| **Separation of Concerns**     | High                        | High                         | High                          |
| **Implementation Effort**      | Medium                      | High                         | High                          |
| **Scalability**                | Good                        | Excellent                    | Excellent                     |
| **Complexity**                 | Medium                      | High                         | Medium                        |
| **Validation Support**         | Low                         | Medium                       | High                          |
| **Dependency Addition**        | None                        | None                         | Yes                           |

## Recommended Approach

**Solution 2: Modular Argument Parsing** emerges as the most suitable approach given the current context and requirements. This solution maintains the modularity of context providers, ensuring each can independently manage its configuration. Although it introduces additional complexity, the benefits in scalability and clarity outweigh the drawbacks. To mitigate the complexity, careful design and potential abstraction layers can be employed.

**Supplementary Recommendation**: Incorporate elements from **Solution 3**, such as using configuration models for validation and type enforcement, to enhance the robustness of the configuration handling without fully adopting a new library.

## Implementation Plan

1. **Refactor Argument Parsing**:
    - Introduce separate namespaces or subparsers in `argparse` for global and provider-specific arguments.
    - Ensure that global arguments (`--model`, `--pretty`, etc.) are parsed independently from context provider arguments.

2. **Update `HermesConfig`**:
    - Modify `HermesConfig` to accommodate separate configuration sections.
    - Implement getters that clearly differentiate between global and provider configurations.

3. **Modify Context Providers**:
    - Adjust each context provider to retrieve its specific configurations from its dedicated section.
    - Ensure that context providers do not interfere with global configurations.

4. **Testing**:
    - Develop comprehensive tests to verify that configurations are correctly parsed and segregated.
    - Validate that global and provider-specific arguments do not clash and are appropriately handled.

5. **Documentation**:
    - Update documentation to reflect the new configuration architecture.
    - Provide usage examples demonstrating the distinction between global and context provider configurations.

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
|  (Separate Parsers)|
+---------+---------+
          |
          v
+-------------------+          +------------------------+
|  GlobalConfig     |          |  ProviderConfig Layers |
| (Global Settings) |          |  (Per Context Provider)|
+---------+---------+          +-----------+------------+
          |                                |
          v                                v
+-------------------+          +------------------------+
|  Hermes Application |        |    Context Providers    |
+-------------------+          +------------------------+
```

## Conclusion

The current configuration handling in Hermes presents clarity and maintainability challenges due to the conflation of global and context provider-specific arguments within a unified `HermesConfig`. Adopting a modular argument parsing strategy, supplemented by structured configuration models, will resolve these issues by establishing clear boundaries between different configuration domains. This approach not only addresses the immediate concerns but also sets a solid foundation for future scalability and maintainability.

