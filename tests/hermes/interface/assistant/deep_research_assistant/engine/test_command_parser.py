from hermes.interface.assistant.deep_research_assistant.engine import CommandParser


def test_parse_activate_subproblems_command():
    expression = """
    <<< activate_subproblems_and_wait
    ///title
    title 1
    ///title
    title 2
    >>>
    """
    results = CommandParser().parse_text(expression)
    assert len(results) == 1
    result = results[0]
    assert len(result.errors) == 0
    assert result.command_name == "activate_subproblems_and_wait"
    assert result.args == {
        "title": ["title 1", "title 2"]
    }