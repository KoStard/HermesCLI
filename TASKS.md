- allow changing the model midway
- add a /reload command to reload the context
- Allow dropping context pieces. Likely they will need to have some IDs that we'll use.
- Add a /ls command that will list what are the included context pieces.
- Allow LLM to request additional context by writing commands
- Allow showing the costs of the API calls
- Allow configuring models with platform/provider/model?
- Consider using ELL: [MadcowD/ell: A language model programming library.](https://github.com/MadcowD/ell)
- Implemenet cache for context providers
- Allow users configure context they want to include with all prompts - in their config folder
- It is actually quite cool that the notebook writes concerns itself. Maybe make that a feature.
- Add <Gap> only as well
- Graceful handling of model output limit exceptions
- Infinite output support
- Live edit mode - the LLM sees what you edited, understands the diffs history, suggests next steps, understands direction.
- Implement integration tests to run before push
- Same for extensions, have a specific place with a specific variable to import.
- Improve how the filename is sent to the LLM, send original name

# Necessary before release
