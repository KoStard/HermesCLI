
def extract_commands(source: str, commands_set: set[str], default_command: str = '/prompt') -> list[tuple[str, str]]:
    """
    Input example:
    some input text
    /command1 arg1 arg2
    some other input text
    /command2 arg1 /command3 arg2
    another input text

    Output:
    [
        ('/prompt', 'some input text'),
        ('/command1', 'arg1 arg2'),
        ('/prompt', 'some other input text'),
        ('/command2', 'arg1'),  
        ('/command3', 'arg2'),
        ('/prompt', 'another input text')
    ]
    """
    result = []
    lines = source.split('\n')
    current_command = None
    current_args = []

    for line in lines:
        line = line.strip()
        words = line.split()
        if words and not (words[0].startswith('/') and words[0][1:] in commands_set):
            if current_command:
                result.append((current_command, ' '.join(current_args)))
                current_args = []
            current_command = default_command
        for word in words:
            if word.startswith('/') and word[1:] in commands_set:
                if current_command:
                    result.append((current_command, ' '.join(current_args)))
                    current_args = []
                current_command = word
            else:
                current_args.append(word)

    if current_command:
        result.append((current_command, ' '.join(current_args)))
    
    return result