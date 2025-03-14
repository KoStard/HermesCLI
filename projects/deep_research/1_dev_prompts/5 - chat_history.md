The assistant API takes messages interface as input.
Each message has an author, either user or assistant.
The first message will be the rendered interface (up-to-date, and updated each time).
Then will be the history of communication at the current focus level. Each time the focus level changes the history will be wiped.
The history gets wiped also when the assistant defines a problem in the beginning.

## Message 1
author: user
{the whole interface}
## Message 2
author: assistant
{some commands executed, preparations, drafts}
## Message 3
author: user

Automatic Reply: The status of the research is "In Progress". Please continue the research or mark it as done.

{optionally, if there were errors, include error report and execution status report.}
...
## Message N
author: assistant
{finishing command}
## Message N+1
author: user
{user sees the latest 3-pager and replies to the assistant for further investigation if needed}
