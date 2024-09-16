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

## 3. Alternatives

### 3.1 Implement Prefills as a New Context Provider
Pros:
- Fits well with the existing architecture
- Can leverage existing context provider loading mechanisms
- Consistent with the current command structure

Cons:
- May require modifications to the context provider base class

### 3.2 Implement Prefills as a Separate System
Pros:
- Keeps prefills distinct from context providers
- Potentially simpler implementation

Cons:
- Requires new loading and processing mechanisms
- Less consistent with the existing architecture

### 3.3 Implement Prefills as a Hybrid System
Pros:
- Combines benefits of both approaches
- Allows for future expansion of prefill functionality

Cons:
- Slightly more complex implementation

## 4. Recommendation
Implement Prefills as a Hybrid System (Alternative 3.3). This approach allows us to leverage the existing context provider structure while keeping prefills as a distinct concept. It provides flexibility for future enhancements and maintains consistency with the current architecture.

## 5. Implementation Details

### 5.1 Prefill Structure
- Prefills will be stored as markdown files in a designated directory (e.g., `~/.config/hermes/prefills/`)
- Each prefill file will use Front Matter for metadata, including required context providers and their attributes
- The main content of the markdown file will be the prefill prompt

### 5.2 PrefillContextProvider
- Create a new `PrefillContextProvider` class that inherits from `ContextProvider`
- This provider will handle loading and processing of prefill files
- It will parse the Front Matter to determine required context providers and their attributes

### 5.3 Prefill Loading Mechanism
- Extend the `extension_loader.py` to include a `load_prefills()` function
- This function will scan the prefills directory and load available prefills
- Prefills will be stored in a dictionary with their names as keys

### 5.4 CLI Integration
- Add a `--prefill` argument to the CLI parser in `main.py`
- When a prefill is specified, load it and its required context providers before starting the chat application

### 5.5 Chat Integration
- Implement a `/prefill` command in the `ChatApplication` class
- When invoked, load the specified prefill and its required context providers
- Apply the prefill prompt to the current chat session

### 5.6 Custom Prefills
- Allow users to add custom prefills in a designated directory (e.g., `~/.config/hermes/custom_prefills/`)
- Extend the prefill loading mechanism to include this directory

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

### 7.2 Implementation Steps
1. Create the `PrefillContextProvider` class
2. Extend `extension_loader.py` to include prefill loading
3. Modify `main.py` to add the `--prefill` CLI argument
4. Update `ChatApplication` to handle the `/prefill` command
5. Implement prefill processing in `ChatApplication`
6. Add support for custom prefills
7. Update documentation and user guide

### 7.3 Questions and Considerations
- How should we handle conflicts between prefill-required context providers and user-specified providers?
- Should we implement a priority system for prefills (e.g., CLI prefills take precedence over in-chat prefills)?
- How can we ensure backward compatibility with existing workflows when introducing prefills?
