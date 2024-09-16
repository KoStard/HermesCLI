# Design Document: Adding Prefills to Hermes

## 1. Context
Hermes is a multi-model chat application with workflow support. The addition of prefills will enhance its functionality by allowing users to save and reuse prompts with additional details. This feature will improve user experience and efficiency.

## 2. Problem Definition
We need to implement a prefill system in Hermes that allows users to:
- Define and save prefills as markdown files with Front Matter metadata
- Access prefills via CLI with `--prefill prefillName`
- Access prefills midway through a chat session with `/prefill PrefillName`
- Specify required context providers and their attributes in the prefill's Front Matter
- Support custom prefills added by users, similar to custom context providers

## 3. Solution: Implement Prefills as a New Context Provider

We will implement prefills as a new context provider, which fits well with the existing architecture of Hermes and allows us to leverage the current context provider loading mechanisms.

### Pros:
- Seamless integration with the existing context provider system
- Consistent with the current command structure
- Can utilize existing loading and processing mechanisms
- Easier to maintain and extend in the future

### Cons:
- May require minor modifications to the context provider base class

## 4. Implementation Details

### 4.1 Prefill Structure
- Prefills will be stored as markdown files in designated directories:
  - Repository prefills: `src/hermes/prefills/`
  - User prefills: `~/.config/hermes/prefills/`
  - Custom prefills: `~/.config/hermes/custom_prefills/`
- Each prefill file will use Front Matter for metadata, including required context providers and their attributes
- The main content of the markdown file will be the prefill prompt

### 4.2 PrefillContextProvider
- Create a new `PrefillContextProvider` class that inherits from `ContextProvider`
- This provider will handle loading and processing of prefill files
- It will parse the Front Matter to determine required context providers and their attributes

### 4.3 Prefill Loading Mechanism
- Modify the `extension_loader.py` to include a `load_prefills()` function
- This function will scan all prefill directories and load available prefills
- Prefills will be stored in a dictionary with their names as keys

### 4.4 CLI Integration
- Add a `--prefill` argument to the CLI parser in `main.py`
- When a prefill is specified, load it and its required context providers before starting the chat application

### 4.5 Chat Integration
- Implement a `/prefill` command in the `ChatApplication` class
- When invoked, load the specified prefill and its required context providers
- Apply the prefill prompt to the current chat session

## 5. Implementation Steps
1. Update `PrefillContextProvider` class to handle loading and processing of prefill files
2. Modify `extension_loader.py` to include prefill loading from all directories
3. Update `main.py` to integrate prefills into the CLI and chat application initialization
4. Modify `ChatApplication` to handle the `/prefill` command and prefill processing
5. Update documentation and user guide

## 6. Think Big
- Implement a prefill management system within Hermes (create, edit, delete prefills)
- Allow sharing and importing of prefills between users
- Create a web interface for managing and using prefills
- Implement prefill versioning and syncing across devices

## 7. Appendix

### 7.1 Sample Prefill File Structure
```yaml
---
name: code_review
required_context_providers:
  file:
    - path: "*.py"
  url:
    - "https://www.python.org/dev/peps/pep-0008/"
---
Please review the provided Python code for adherence to PEP 8 style guide and best practices. 
Provide suggestions for improvements and explain any potential issues you find.
```

### 7.2 Questions and Considerations
- How should we handle conflicts between prefill-required context providers and user-specified providers?
- Should we implement a priority system for prefills (e.g., CLI prefills take precedence over in-chat prefills)?
- How can we ensure backward compatibility with existing workflows when introducing prefills?
