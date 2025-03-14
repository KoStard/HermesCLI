If there were any errors with processing the assistant commands, collect report about them, as detailed as possible without exposing the internals of the system.
Include report about errors in the automatic message back to the assistant.

```
Automatic Reply: The status of the research is "In Progress". Please continue the research or mark it as done.

### Errors report:
#### Error 1
... {include details about the line of the error and more}
#### ...

### Execution Status Report:
- Command 'command_name' failed: reason for failure

{depends: As there were errors, not changing scope until they are resolved}
{depends: As there were errors, not finishing until they are resolved}
{depends: Not executing any command as there was syntax issue}
```

If there are any errors, don't finish the execution or allow moving focus, go back to the assistant, make sure everything is clean, only then allow finishing or moving focus.
Other commands not impacting the history can run, unless there is syntax error, in which case inform in the error report that the commands were not executed.

The Execution Status Report is included when commands fail during execution (as opposed to syntax errors which prevent execution). This helps the assistant understand which commands were attempted but failed, and why they failed.
