- history recovery feature
- when loading extensions, they might fail, it should not crash the app, instead it should log the error and move on
- allow changing the model midway
- allow saving and loading chat
- add a /reload command to reload the context
- Allow dropping context pieces. Likely they will need to have some IDs that we'll use.
- Add a /ls command that will list what are the included context pieces.
- Allow LLM to request additional context by writing commands
- Allow showing the costs of the API calls
- Allow configuring models with platform/provider/model?
- Add proper error message when in config you have an invalid model name
- Dedupe context providers
- Add alias --create for --update
- Consider using ELL: [MadcowD/ell: A language model programming library.](https://github.com/MadcowD/ell)
- Implemenet cache for context providers
- Allow users configure context they want to include with all prompts - in their config folder
- It is actually quite cool that the notebook writes concerns itself. Maybe make that a feature.
- How to make the results formatted like markdown code, without actually rendering it - syntax highlighting
- Add <Gap> only as well
- Graceful handling of model output limit exceptions
- Infinite output support
- Live edit mode - the LLM sees what you edited, understands the diffs history, suggests next steps, understands direction.
- Implement integration tests to run before push
- Context providers import should be hardcoded list, instead of file detection. Likely slows down a lot. Same for extensions, have a specific place with a specific variable to import.
- Improve how the filename is sent to the LLM, send original name
- Debugging toolchain

# Necessary before release

- Allow loading chat from CLI argument
- Handle LLM exceptions
- Ctrl+c while inputting should just invalidate
- Fix the gemini model access - client name is incorrect

