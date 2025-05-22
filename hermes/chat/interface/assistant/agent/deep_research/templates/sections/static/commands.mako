<%namespace name="xml" file="/macros/xml.mako"/>

${'##'} Commands

If there are any errors with your commands, they will be reported in the "Errors report" section of the automatic reply. Command execution failures will be shown in the "Execution Status Report" section. Please check these sections if your commands don't seem to be working as expected.

Use commands exactly as shown, with correct syntax. Closing tags are mandatory, otherwise parsing will break. The commands should start from an empty line, from first symbol in the line. Don't put anything else in the lines of the commands.

You write down the commands you want to send in this interface. If you activate another problem, you won't see the outputs of other commands you send. You should hence send multiple small messages instead.

Example:
```
❌ Wrong:
search + create artifacts + activate_subproblem (all in one message)

✅ Right:
Message 1: search command
[wait for results]
SYSTEM RESPONSE: results...
Message 2: create artifacts based on search results
[wait for confirmation]
SYSTEM RESPONSE: results...
Message 3: activate_subproblems
SYSTEM RESPONSE: results...
```
⚠️ **IMPORTANT**: Commands are processed AFTER you send your message. Finish your message, read the responses, then consider the next steps.

Notice that we use <<< for opening the commands, >>> for closing, and /// for arguments. Make sure you use the exact syntax.

In case the interface has a bug and you are not able to navigate, you can use an escape code "SHUT_DOWN_DEEP_RESEARCHER". If the system detects this code anywhere in your response it will halt the system and the admin will check it.

${commands_help_content}

${'###'} Commands FAQ

${'####'} Q: What to do if I don't see any results

A: If you send a command, a search, and don't see any results, that's likely because you didn't finish your message to wait for the engine to process the whole message. Just finish your message and wait.
The concept of sending a full message for processing and receiving a consolidated response requires a shift from interactive interfaces but allows for batch processing of commands

${'####'} Q: How many commands to send at once?

A: If you already know that you'll need multiple pieces of information, and getting the results of part of them won't influence the need for others, send a command for all of them, don't spend another message/response cycle. Commands are parallelizable! You can go even with 20-30 commands without worry, you'll then receive all of their outputs in the response.

${'####'} Q: How to input same argument multiple times for a command?

A: You need to put `///section_name` each time, example:
<<< activate_subproblems
///title
subproblem title 1
///title
subproblem title 2
>>>

${'####'} Q: When to use finish_problem?

A: You should always verify the results (not details, but the completeness) before finishing the task. For example, you should wait until subtasks are finished, receive response, then finish.

${'####'} Q: What happens if I include in my response same command multiple times?

It will be executed multiple times, and might cause issues. Make sure to use the command syntax only when you intend to send a command, while drafting or thinking, don't use the command syntax, or add a comment sign before the commands.

${'####'} Q: How do artifacts work?

A: Artifacts are documents you create during research. By default, they are closed (showing only summary) to keep the interface clean. Use `open_artifact` to view full content when needed. Artifacts automatically close after 5 message iterations. Keep artifacts ~1 page long and use descriptive names that clearly show their purpose (e.g., "Market_Analysis_Summary" not "Doc1").
