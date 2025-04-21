## Template for formatting new user instructions injected into AutoReply
<%namespace name="xml" file="/macros/xml.mako"/>
## Context variables expected:
## - instruction: str (The raw user instruction)

A new instruction has arrived from the user regarding the current research context.
Please analyze the following instruction and take appropriate actions using the available commands.
Remember to check existing artifacts, subproblems, and knowledge base entries before creating new ones.
When you have fully addressed the instruction, use the `finish_problem` command on the current (root) node to signal completion and readiness for the next user instruction.

<user_instruction>
${instruction}
</user_instruction>
