import pytest
from pathlib import Path

# Assuming your tests run from the root of the git repository
# Adjust the path if necessary based on your test execution context
TEMPLATE_DIR = Path("hermes/interface/assistant/deep_research_assistant/engine/templates")

# Make sure the template directory exists before running tests
if not TEMPLATE_DIR.exists():
    raise FileNotFoundError(
        f"Template directory not found: {TEMPLATE_DIR.resolve()}. "
        "Ensure tests are run from the project root or adjust TEMPLATE_DIR."
    )
if not (TEMPLATE_DIR / "context/auto_reply.mako").exists():
     raise FileNotFoundError(
        f"auto_reply.mako not found in {TEMPLATE_DIR.resolve()}/context. "
        "Ensure the template file exists."
    )
if not (TEMPLATE_DIR / "macros/xml.mako").exists():
     raise FileNotFoundError(
        f"xml.mako not found in {TEMPLATE_DIR.resolve()}/macros. "
        "Ensure the macro file exists."
    )


# Import necessary classes AFTER checking path existence
from hermes.interface.assistant.deep_research_assistant.engine.context.history import AutoReply
from hermes.interface.assistant.deep_research_assistant.engine.templates.template_manager import TemplateManager


@pytest.fixture(scope="module")
def template_manager() -> TemplateManager:
    """Provides a TemplateManager instance for the tests."""
    return TemplateManager(template_dir=str(TEMPLATE_DIR))


def test_generate_auto_reply_empty(template_manager):
    """Test rendering an empty AutoReply."""
    auto_reply = AutoReply(
        error_report="",
        command_outputs=[],
        messages=[],
        confirmation_request=None,
        dynamic_sections=[],
    )
    output = auto_reply.generate_auto_reply(template_manager)

    assert "# Automatic Reply" in output
    assert "### Command Outputs" in output
    assert "No command outputs" in output
    assert "Confirmation Required" not in output
    assert "Internal Automatic Messages" not in output
    assert "Updated Interface Sections" not in output


def test_generate_auto_reply_with_error(template_manager):
    """Test rendering with only an error report."""
    error_msg = "Something went wrong!"
    auto_reply = AutoReply(
        error_report=error_msg,
        command_outputs=[],
        messages=[],
        confirmation_request=None,
        dynamic_sections=[],
    )
    output = auto_reply.generate_auto_reply(template_manager)

    assert """
# Automatic Reply

If there are commands you sent in your message and they have any errors or outputs, you'll see them below.
If you don't see a command report, then no commands were executed!

Something went wrong!

### Command Outputs

No command outputs

""" == output


def test_generate_auto_reply_with_confirmation(template_manager):
    """Test rendering with only a confirmation request."""
    confirmation_msg = "Are you sure you want to proceed?"
    auto_reply = AutoReply(
        error_report="",
        command_outputs=[],
        messages=[],
        confirmation_request=confirmation_msg,
        dynamic_sections=[],
    )
    output = auto_reply.generate_auto_reply(template_manager)

    assert "# Automatic Reply" in output
    assert "### Confirmation Required" in output
    assert confirmation_msg in output
    assert "### Command Outputs" in output
    assert "No command outputs" in output


def test_generate_auto_reply_with_commands(template_manager):
    """Test rendering with command outputs."""
    command_outputs = [
        ("command1", {"args": {"arg1": "val1"}, "output": "Output 1"}),
        ("command2", {"args": {}, "output": "Output 2"}),
    ]
    auto_reply = AutoReply(
        error_report="",
        command_outputs=command_outputs,
        messages=[],
        confirmation_request=None,
        dynamic_sections=[],
    )
    output = auto_reply.generate_auto_reply(template_manager)

    assert "# Automatic Reply" in output
    assert "### Command Outputs" in output
    assert "#### <<< command1" in output
    assert "Arguments: arg1: val1" in output
    assert "Output 1" in output
    assert "#### <<< command2" in output
    # Check no args line for cmd2 by splitting the output around the command marker
    # and checking the part before the first code block fence
    command2_section = output.split("#### <<< command2")[1]
    header_before_code = command2_section.split("```")[0]
    assert "Arguments:" not in header_before_code
    assert "Output 2" in output
    assert "No command outputs" not in output


def test_generate_auto_reply_with_command_truncation(template_manager):
    """Test rendering with truncated command output."""
    long_output = "This is line one.\nThis is line two.\nThis is line three."
    command_outputs = [
        ("long_command", {"args": {}, "output": long_output}),
    ]
    max_len = 30 # Truncates after "This is line one."
    auto_reply = AutoReply(
        error_report="",
        command_outputs=command_outputs,
        messages=[],
        confirmation_request=None,
        dynamic_sections=[],
    )
    output = auto_reply.generate_auto_reply(
        template_manager, per_command_output_maximum_length=max_len
    )

    expected_truncated = "This is line one."
    truncation_help = "Note: To see the full content again, rerun the command."

    assert "# Automatic Reply" in output
    assert "### Command Outputs" in output
    assert "#### <<< long_command" in output
    # Check that the truncated output is present, along with the help message
    # Use repr() to make debugging easier with newlines
    expected_block = f"```\n{expected_truncated}\n\n[...38 characters omitted (69.1% of content)]\n\n{truncation_help}\n```"
    assert expected_block in output, f"Expected block not found in output:\n{output}\nExpected:\n{expected_block}"
    assert "This is line two." not in output # Ensure the rest is gone


def test_generate_auto_reply_with_internal_messages(template_manager):
    """Test rendering with internal messages."""
    messages = [
        ("Message from node A", "Node A Title"),
        ("Another message from B", "Node B Title"),
    ]
    auto_reply = AutoReply(
        error_report="",
        command_outputs=[],
        messages=messages,
        confirmation_request=None,
        dynamic_sections=[],
    )
    output = auto_reply.generate_auto_reply(template_manager)

    assert "# Automatic Reply" in output
    assert "### Internal Automatic Messages" in output
    assert "#### From: Node A Title" in output
    assert "```\nMessage from node A\n```" in output
    assert "#### From: Node B Title" in output
    assert "```\nAnother message from B\n```" in output


def test_generate_auto_reply_with_dynamic_sections(template_manager):
    """Test rendering with dynamic sections."""
    dynamic_sections = [
        (0, "## Section 0\nContent Zero"),
        (2, "## Section 2\nContent Two"),
    ]
    auto_reply = AutoReply(
        error_report="",
        command_outputs=[],
        messages=[],
        confirmation_request=None,
        dynamic_sections=dynamic_sections,
    )
    output = auto_reply.generate_auto_reply(template_manager)

    assert "# Automatic Reply" in output
    assert "### Updated Interface Sections" in output
    assert "The following interface sections have been updated:" in output
    assert "## Section 0\nContent Zero" in output
    assert "## Section 2\nContent Two" in output


def test_generate_auto_reply_combined(template_manager):
    """Test rendering with a combination of elements."""
    error_msg = "Minor issue detected."
    confirmation_msg = "Confirm action?"
    command_outputs = [("cmd", {"args": {}, "output": "Cmd Output"})]
    messages = [("Internal note", "Origin Node")]
    dynamic_sections = [(1, "## Updated Section 1\nNew content")]

    auto_reply = AutoReply(
        error_report=error_msg,
        command_outputs=command_outputs,
        messages=messages,
        confirmation_request=confirmation_msg,
        dynamic_sections=dynamic_sections,
    )
    output = auto_reply.generate_auto_reply(template_manager, per_command_output_maximum_length=50)

    # Check presence of all sections in rough order
    assert "# Automatic Reply" in output
    assert "### Confirmation Required" in output
    assert confirmation_msg in output
    assert error_msg in output # Error comes after confirmation
    assert "### Command Outputs" in output
    assert "#### <<< cmd" in output
    assert "```\nCmd Output\n```" in output
    assert "### Internal Automatic Messages" in output
    assert "#### From: Origin Node" in output
    assert "```\nInternal note\n```" in output
    assert "### Updated Interface Sections" in output
    assert "## Updated Section 1\nNew content" in output
