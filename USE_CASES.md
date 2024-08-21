# Hermes Use Cases

## 1. Context-Aware File Analysis
**Need**: Analyze multiple documents for a project.
**Usage**: User runs Hermes with Claude model and multiple file inputs.
**Action**: Hermes processes files and allows user to ask questions about their content.
**Outcome**: User gains insights across multiple documents efficiently.

## 2. Immediate Prompt Execution
**Need**: Quick answer to a specific question about a document.
**Usage**: User runs Hermes with a file and --prompt option.
**Action**: Hermes sends the prompt and file content to the AI model immediately.
**Outcome**: User receives an instant response without entering the chat interface.

## 3. Collaborative Document Editing
**Need**: Improve a draft document with AI assistance.
**Usage**: User runs Hermes with a file and --update option.
**Action**: Hermes allows user to discuss the document and apply AI suggestions directly.
**Outcome**: Document is updated with AI-assisted improvements.

## 4. Research Note-Taking
**Need**: Compile research notes from an AI conversation.
**Usage**: User runs Hermes with --append option pointing to a notes file.
**Action**: Hermes appends AI responses to the specified file during the conversation.
**Outcome**: User builds a comprehensive set of notes from the AI interaction.

## 5. Careful API Usage
**Need**: Avoid accidental API calls and associated costs.
**Usage**: User runs Hermes with --confirm-before-starting flag.
**Action**: Hermes prompts for confirmation before sending any requests to the AI model.
**Outcome**: User has control over when API calls are made, preventing unintended usage.

## 6. Local Model Interaction
**Need**: Work with AI models without internet connection or for privacy.
**Usage**: User runs Hermes with Ollama model option.
**Action**: Hermes connects to locally running Ollama for AI interactions.
**Outcome**: User can work with AI models offline or with enhanced privacy.

## 7. Image Analysis (for supported models)
**Need**: Analyze or describe an image.
**Usage**: User runs Hermes with a supported model and an image file.
**Action**: Hermes processes the image and allows user to ask questions about it.
**Outcome**: User receives AI-generated analysis or description of the image.

## 8. Custom Prompt Templates
**Need**: Use a pre-defined prompt structure for consistent interactions.
**Usage**: User creates a prompt file and runs Hermes with --prompt-file option.
**Action**: Hermes uses the custom prompt to initiate the conversation with the AI.
**Outcome**: User maintains consistency in AI interactions across multiple sessions.
