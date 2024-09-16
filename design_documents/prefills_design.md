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
Implement get_dependent_context_providers, which should return a list[(str, str)], with first value being the key and second value being the initialisation string, same as it's when the user adds context from CLI.
The front matter in the markdown should be like this as well, without any additional complexities.
The base class should be modified of context providers with default implemented of get_dependent_context_providers returning empty list.
During the load phase of the context provider, the prefills context provider should load the markdown files with the prefills with all the details.


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
- Each prefill file will use Front Matter for metadata, including required context providers and their attributes
- The main content of the markdown file will be the prefill prompt

### 4.2 PrefillContextProvider
- Create a new `PrefillContextProvider` class that inherits from `ContextProvider`
- This provider will handle loading and processing of prefill files
- It will parse the Front Matter to determine required context providers and their attributes
- Should handle loading from the custom folder as well

