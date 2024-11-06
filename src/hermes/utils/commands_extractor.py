def extract_commands(source: str, commands_set: set[str], default_command: str = '/prompt') -> list[tuple[str, str]]:
    """
    Extracts commands and their arguments from the input text.
    - Each line starting with '/' is treated as a command (first word) with arguments (rest of line)
    - Lines without commands are treated as text and combined with adjacent text lines
    - Each command can only have arguments in its own line

    Input example:
    some input 
    text
    /command1 arg1 arg2
    some other input text
    /command2 arg1 arg2
    another input text

    Output:
    [
        ('/prompt', 'some input\ntext'),
        ('/command1', 'arg1 arg2'),
        ('/prompt', 'some other input text'),
        ('/command2', 'arg1 arg2'),
        ('/prompt', 'another input text')
    ]
    """
    result = []
    lines = source.split('\n')
    current_text_lines = []

    def flush_text_buffer():
        if current_text_lines:
            result.append((default_command, '\n'.join(current_text_lines)))
            current_text_lines.clear()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        words = line.split()
        if words and words[0].startswith('/') and words[0][1:] in commands_set:
            # Found a command - first flush any accumulated text
            flush_text_buffer()
            # Add command with its arguments
            command = words[0]
            args = ' '.join(words[1:]) if len(words) > 1 else ''
            result.append((command, args))
        else:
            # Regular text line - accumulate it
            current_text_lines.append(line)

    # Don't forget to flush any remaining text
    flush_text_buffer()
    
    return result