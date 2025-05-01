# Design Document: Help Text Generation for Command Framework

## Problem Statement
Task 1, item 10 requires adding "Help text generation/access mechanisms" to the core `hermes.interface.commands` package. Currently, help text functionality exists in Deep Research Assistant (DRA) using a Mako template, but we need to create a generalized mechanism in the core package that can be used across different interfaces.

## Requirements
1. Provide a way to generate help text for commands in the core package
2. Keep using mako templates. The template engine is generic and we can have a mako template file in the commands directory

## Current State
Currently, help text generation is handled in the DRA through:
- `Command` and `CommandSection` classes store help text as attributes
- A Mako template (`command_help.mako`) renders command help documentation in deep research
- The template is specific to DRA and not available to other interfaces
- The TemplateManager currently accepts only one templates directory, which limits our ability to store them in multiple places
- Maintain the original template file

## Proposed Solution Options

### Option 1: Template-Based Help Text Generator in Core Package
- Create a `CommandHelpGenerator` class in the core package that utilizes Mako templates
- Include a default template with the package for standard help text formatting
- Allow interfaces to override the template if they need custom formatting
- Provide methods to generate help for a single command or all commands

**Pros:**
- Consistent help text generation across interfaces
- Leverages existing Mako template engine
- Flexible - interfaces can customize the template if needed
- Consistent with existing DRA implementation

**Cons:**
- Adds dependency on template management
- Requires additional template file to be distributed with package

### Option 2: Simple Text-Based Help Generator
- Create a simple text-based help generator that doesn't depend on templates
- Output plain text or markdown representation of command help
- Generate help text programmatically based on command metadata

**Pros:**
- Simpler implementation with no template dependency
- No need for template file management
- Potentially easier to use for new interfaces

**Cons:**
- Less flexible formatting options
- Inconsistent with existing template-based approach in DRA
- Would require DRA to maintain two ways of generating help

### Option 3: Registry-Based Help Formatter
- Define a base `HelpFormatter` class and a registry of formatters
- Provide standard formatters for common output formats (plain text, markdown, etc.)
- Interfaces register custom formatters for specialized output

**Pros:**
- Maximum flexibility for different output formats
- Cleanly separates formatting logic from command metadata
- Follows the registry pattern already used in the command framework

**Cons:**
- More complex implementation
- Adds another registry to maintain
- Might be overkill for the current needs

## Conclusion

After analyzing the options, we've decided to implement Option 1: A Template-Based Help Text Generator. 

This approach:
1. Creates a `CommandHelpGenerator` class in the core package
2. Uses the existing `TemplateManager` infrastructure
3. Provides a default template for standard help formatting
4. Allows interfaces to override with custom templates if needed

The implementation includes:
- A default help template (`templates/command_help.mako`) in the core package
- A `CommandHelpGenerator` class with methods for generating help text
- Integration with the existing command registry

This solution provides a good balance of consistency, flexibility, and integration with existing patterns while meeting the requirement of providing help text generation across different interfaces.
