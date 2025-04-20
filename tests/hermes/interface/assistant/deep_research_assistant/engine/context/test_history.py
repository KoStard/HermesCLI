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


from unittest.mock import MagicMock, Mock

# Import necessary classes AFTER checking path existence
from hermes.interface.assistant.deep_research_assistant.engine.context.history import AutoReply, AutoReplyAggregator, ChatHistory, ChatMessage
from hermes.interface.assistant.deep_research_assistant.engine.templates.template_manager import TemplateManager
# Import new dynamic section components
from hermes.interface.assistant.deep_research_assistant.engine.context.dynamic_sections import RendererRegistry, create_renderer_registry
from hermes.interface.assistant.deep_research_assistant.engine.context.dynamic_sections.base import (
    DynamicSectionData, HeaderSectionData, PermanentLogsData, BudgetSectionData, KnowledgeBaseData # Add others as needed
)
from hermes.interface.assistant.deep_research_assistant.engine.context.dynamic_sections.base import DynamicSectionRenderer


@pytest.fixture(scope="module")
def template_manager() -> TemplateManager:
    """Provides a TemplateManager instance for the tests."""
    # Ensure Mako can find the templates relative to the test execution path
    return TemplateManager(template_dir=str(TEMPLATE_DIR.resolve()))

@pytest.fixture(scope="module")
def renderer_registry(template_manager: TemplateManager) -> RendererRegistry:
    """Provides a real renderer registry for integration testing the template."""
    # We use the real registry to ensure templates are found and render correctly
    return create_renderer_registry(template_manager)

# --- Mock Renderer for focused unit tests ---
class MockRenderer(DynamicSectionRenderer):
     def __init__(self):
         # No TemplateManager needed for mock
         pass
     def render(self, data: DynamicSectionData, future_changes: int) -> str:
         # Simple mock render: return data type and future changes
         return f"Rendered {type(data).__name__} (future_changes={future_changes})"

@pytest.fixture
def mock_renderer_registry() -> RendererRegistry:
    """Provides a registry with mock renderers."""
    # Use specific data types you want to test with mocks
    return {
        HeaderSectionData: MockRenderer(),
        PermanentLogsData: MockRenderer(),
        BudgetSectionData: MockRenderer(),
        KnowledgeBaseData: MockRenderer(),
        # Add other types with MockRenderer() if needed for specific tests
    }


def test_generate_auto_reply_empty(template_manager, renderer_registry):
    """Test rendering an empty AutoReply with real templates."""
    auto_reply = AutoReply(
        error_report="",
        command_outputs=[],
        messages=[],
        confirmation_request=None,
        dynamic_sections=[], # Empty list of (index, data_instance)
    )
    output = auto_reply.generate_auto_reply(
        template_manager=template_manager,
        renderer_registry=renderer_registry,
        future_changes_map={},
        per_command_output_maximum_length=None,
    )

    assert "# Automatic Reply" in output
    assert "### Command Outputs" in output
    assert "No command outputs" in output
    assert "Confirmation Required" not in output
    assert "Internal Automatic Messages" not in output
    assert "Updated Interface Sections" not in output


def test_generate_auto_reply_with_error(template_manager, renderer_registry):
    """Test rendering with only an error report."""
    error_msg = "Something went wrong!"
    auto_reply = AutoReply(
        error_report=error_msg,
        command_outputs=[],
        messages=[],
        confirmation_request=None,
        dynamic_sections=[],
    )
    output = auto_reply.generate_auto_reply(
        template_manager=template_manager,
        renderer_registry=renderer_registry,
        future_changes_map={},
        per_command_output_maximum_length=None,
    )

    # Exact output might change slightly due to whitespace, check key parts
    assert "# Automatic Reply" in output
    assert "Something went wrong!" in output # The error report itself
    assert "### Command Outputs" in output
    assert "No command outputs" in output


def test_generate_auto_reply_with_confirmation(template_manager, renderer_registry):
    """Test rendering with only a confirmation request."""
    confirmation_msg = "Are you sure you want to proceed?"
    auto_reply = AutoReply(
        error_report="",
        command_outputs=[],
        messages=[],
        confirmation_request=confirmation_msg,
        dynamic_sections=[],
    )
    output = auto_reply.generate_auto_reply(
        template_manager=template_manager,
        renderer_registry=renderer_registry,
        future_changes_map={},
        per_command_output_maximum_length=None,
    )

    assert "# Automatic Reply" in output
    assert "### Confirmation Required" in output
    assert confirmation_msg in output
    assert "### Command Outputs" in output
    assert "No command outputs" in output


def test_generate_auto_reply_with_commands(template_manager, renderer_registry):
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
    output = auto_reply.generate_auto_reply(
        template_manager=template_manager,
        renderer_registry=renderer_registry,
        future_changes_map={},
        per_command_output_maximum_length=None,
    )

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


def test_generate_auto_reply_with_command_truncation(template_manager, renderer_registry):
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
        template_manager=template_manager,
        renderer_registry=renderer_registry,
        future_changes_map={},
        per_command_output_maximum_length=max_len,
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


def test_generate_auto_reply_with_internal_messages(template_manager, renderer_registry):
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
    output = auto_reply.generate_auto_reply(
        template_manager=template_manager,
        renderer_registry=renderer_registry,
        future_changes_map={},
        per_command_output_maximum_length=None,
    )

    assert "# Automatic Reply" in output
    assert "### Internal Automatic Messages" in output
    assert "#### From: Node A Title" in output
    assert "```\nMessage from node A\n```" in output
    assert "#### From: Node B Title" in output
    assert "```\nAnother message from B\n```" in output


# --- Tests for New Dynamic Section Logic ---

def test_generate_auto_reply_with_dynamic_sections(mock_renderer_registry):
    """Test rendering with dynamic sections using mock renderers."""
    # Use mock data classes
    dynamic_sections_data = [
        (0, HeaderSectionData()), # Index 0
        (3, BudgetSectionData(budget=100, remaining_budget=50)), # Index 3
    ]
    auto_reply = AutoReply(
        error_report="", command_outputs=[], messages=[], confirmation_request=None,
        dynamic_sections=dynamic_sections_data,
    )
    # Mock template manager - not used by mock renderers
    mock_tm = MagicMock(spec=TemplateManager)

    # Test case 1: No future changes
    future_changes_map_1 = {}
    output1 = auto_reply.generate_auto_reply(
        mock_tm, mock_renderer_registry, future_changes_map_1, None
    )
    assert "# Automatic Reply" in output1
    assert "### Updated Interface Sections" in output1
    assert "Rendered HeaderSectionData (future_changes=0)" in output1
    assert "Rendered BudgetSectionData (future_changes=0)" in output1

    # Test case 2: Section 0 changes later
    future_changes_map_2 = {0: 1} # Index 0 changes 1 time later
    output2 = auto_reply.generate_auto_reply(
        mock_tm, mock_renderer_registry, future_changes_map_2, None
    )
    assert "Rendered HeaderSectionData (future_changes=1)" in output2
    assert "Rendered BudgetSectionData (future_changes=0)" in output2 # Index 3 didn't change later

    # Test case 3: Both sections change later
    future_changes_map_3 = {0: 2, 3: 1}
    output3 = auto_reply.generate_auto_reply(
        mock_tm, mock_renderer_registry, future_changes_map_3, None
    )
    assert "Rendered HeaderSectionData (future_changes=2)" in output3
    assert "Rendered BudgetSectionData (future_changes=1)" in output3


def test_knowledge_base_hiding_with_future_changes(template_manager, renderer_registry):
    """Test that KnowledgeBaseRenderer hides content if future_changes > 0."""
    # Use the *real* KnowledgeBaseRenderer via the real registry
    kb_data = KnowledgeBaseData(knowledge_base=[]) # Empty KB for simplicity
    dynamic_sections_data = [(8, kb_data)] # Assuming KB is index 8 based on DYNAMIC_SECTION_ORDER

    auto_reply = AutoReply("", [], [], None, dynamic_sections=dynamic_sections_data)

    # Case 1: No future changes (should render normally)
    output_no_change = auto_reply.generate_auto_reply(
        template_manager, renderer_registry, {}, None
    )
    assert "# Shared Knowledge Base" in output_no_change
    assert "No knowledge entries added yet" in output_no_change # Content from template
    assert "[Knowledge Base content omitted" not in output_no_change

    # Case 2: Future changes > 0 (should render placeholder)
    output_with_change = auto_reply.generate_auto_reply(
        template_manager, renderer_registry, {8: 1}, None # Index 8 changes later
    )
    assert "# Shared Knowledge Base" not in output_with_change # The header might be omitted too depending on renderer impl.
    assert "<knowledge_base>" in output_with_change # Check for the wrapper tag
    assert "[Knowledge Base content omitted" in output_with_change
    assert "No knowledge entries added yet" not in output_with_change


def test_renderer_error_handling(mock_renderer_registry):
    """Test the error message generated when a renderer fails."""
    # Create a renderer that will raise an exception
    class FailingRenderer(MockRenderer):
        def render(self, data: DynamicSectionData, future_changes: int) -> str:
            raise ValueError("Simulated rendering error")

    # Add the failing renderer to the mock registry
    mock_registry = mock_renderer_registry.copy()
    mock_registry[PermanentLogsData] = FailingRenderer() # Replace log renderer

    dynamic_sections_data = [
        (1, PermanentLogsData(permanent_logs=["log1"])) # Index 1
    ]
    auto_reply = AutoReply("", [], [], None, dynamic_sections=dynamic_sections_data)
    mock_tm = MagicMock(spec=TemplateManager)

    output = auto_reply.generate_auto_reply(mock_tm, mock_registry, {}, None)

    assert "### Updated Interface Sections" in output
    assert "<error context=\"Rendering dynamic section index 1 (PermanentLogsData)\">" in output
    assert "**SYSTEM ERROR:** Failed to render this section." in output
    assert "Please create an artifact named 'render_error_section_1_PermanentLogsData'" in output
    assert "ValueError: Simulated rendering error" in output # Check traceback is included


def test_generate_auto_reply_combined(template_manager, renderer_registry):
    """Test rendering with a combination of elements and real templates."""
    error_msg = "Minor issue detected."
    confirmation_msg = "Confirm action?"
    command_outputs = [("cmd", {"args": {}, "output": "Cmd Output"})]
    messages = [("Internal note", "Origin Node")]
    # Use real data objects
    dynamic_sections_data = [
        (2, BudgetSectionData(budget=50, remaining_budget=10)), # Index 2
        (8, KnowledgeBaseData(knowledge_base=[]))             # Index 8
    ]
    future_changes_map = {8: 1} # KB changes later

    auto_reply = AutoReply(
        error_report=error_msg,
        command_outputs=command_outputs,
        messages=messages,
        confirmation_request=confirmation_msg,
        dynamic_sections=dynamic_sections_data,
    )
    output = auto_reply.generate_auto_reply(
        template_manager, renderer_registry, future_changes_map,
        per_command_output_maximum_length=50 # Test truncation as well
    )

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
    # Check presence of all sections in rough order
    assert "# Automatic Reply" in output
    assert "### Confirmation Required" in output
    assert confirmation_msg in output
    assert error_msg in output # Error comes after confirmation
    assert "### Command Outputs" in output
    assert "#### <<< cmd" in output
    # Check command output truncation (50 chars max, Cmd Output is short)
    assert "```\nCmd Output\n```" in output
    assert "### Internal Automatic Messages" in output
    assert "#### From: Origin Node" in output
    assert "```\nInternal note\n```" in output
    assert "### Updated Interface Sections" in output
    # Check Budget rendering (Index 2, future_changes=0)
    assert "# Budget Information" in output
    assert "Remaining: 10 message cycles" in output
    assert "Status: LOW" in output # Check budget status logic
    # Check KnowledgeBase rendering (Index 8, future_changes=1 -> omitted)
    assert "# Shared Knowledge Base" not in output # Header omitted by renderer
    assert "[Knowledge Base content omitted" in output
