## Template for formatting new user instructions injected into AutoReply
## Context variables expected:
## - instruction: str (The raw user instruction)

A new instruction has arrived from the user regarding the current research context.
Please analyze the following instruction, append to the problem definition, and take appropriate actions. Updating the problem definition will allow your team members clearly see the change in your direction.
When you have fully addressed the instruction, use the `finish_problem` command on the current (root) node to signal completion and readiness for the next user instruction.

<user_instruction>
${instruction}
</user_instruction>
