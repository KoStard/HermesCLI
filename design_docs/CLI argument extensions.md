Currently Hermes can receive input from CLI in the following ways:
- `--text` - provide textual input that will become part of the first prompt being sent
- `file1 file2` list files that will be part of the first message
- `--prompt` in case you don't want to input from terminal and just want to pass the first input from the CLI

But now I see that this is not enough.
I want to have the freedom to have more context providers.
Something like `--url ...`
This design should also support extensions. There should be a folder, where the users can add their own extensions, which will add new CLI arguments `--...`, and allow them to implement how these inputs will be processed.

The context providers will update the ArgumentParser to add its arguments there, then later from the parser arguments it will extract and save the values. Later it will be called to add to the prompt builder.

So, we should have a base class for the idea of context provider (we should consider if the word context is the best one, are there better names?).
```python
T = TypeVar('T')  # Define a type variable

class ContextProvider(ABC):
	@abstractmethod
	def add_argument(self, parser: ArgumentParser):
		pass

	@abstractmethod
	def load_context(self, args):
		pass

	# Will use the available prompt builder methods to add these context pieces to it
	@abstractmethod
	def add_to_prompt(self, prompt_builder):
		pass

```

Currently there is no such concept as prompt builder. We only have prompt formatter, which receives everything at once and generates the first message. Instead, we should refactor these to use builder patter.

```python
class PromptBuilder(ABC):
    @abstractmethod
    def add_text(self, text, name=None):
	    # The text piece being added might have a name, such that it allows the user to reference it from another piece
	    pass
	def add_file
	def add_image
	def build_prompt
```

Then we'll have `XmlPromptBuilder` and `BedrockPromptBuilder` implementations. Then the prompt builder will be used by the context providers to add to the prompt.

Then we should have the default context providers implemented, these will be the files context provider (using add_file method), the text context provider, and new ones, a URL context provider (add_text with a name) and an image input (using add_image).
The URL context provider should read the URL (with retry mechanism using tenacity), and convert it to markdown text.

Tasks:
- [x] Review alternatives and agree on names for these concepts
- [x] Define the context provider base class
- [x] Define the prompt builder base class
- [x] Implement the file context provider
- [x] Implement the text context provider
- [x] Implement unit tests for these
- [x] Implement context orchestrator, that will handle loading and using the context providers. This part should be flexible enough that later we'll add extension model.
- [x] Add logic into the main.py that will use the context orchestrator, update the arguments, etc.
- [x] Implement the prompt builders based on the existing prompt_formatters.
- [x] Implement unit tests for the prompt builders.
- [x] Update the chat application to use prompt builders and context providers.
- [x] Final update of main.py
- [x] Deprecate prompt formatters.
- [x] Update unit-tests for main.py
- [ ] Update the workflow execution to use this model. Update tests.
- [ ] Manual Test of main.py
- [ ] Add the URL provider and tests
- [ ] Add image provider and tests