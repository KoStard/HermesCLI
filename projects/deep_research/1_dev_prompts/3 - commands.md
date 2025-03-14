Some additional instructions for the commands:

## add_subproblem
- If there is a subproblem with such title, don't add it again

## add_criteria
- If there is an entry with such title, don't add it again

## add_criteria_to_subproblem
- Allows adding criteria to a specific subproblem by title
- If there is an entry with such title in the specified subproblem, don't add it again
- The criteria should be a single line (will be sanitized during processing)

## add_attachment
- the assistant can create attachments that support the current findings

# Instructions
- The assistant can enter multiple commands at once, including one line and multiline
- In a long response, the assistant CANNOT do more than one focus change. Also no further commands are allowed afterwards.
