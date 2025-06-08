import json


def _load_notebook(ipynb_path):
    """Load notebook from path and return JSON content."""
    with open(ipynb_path, encoding="utf-8") as f:
        return json.load(f)


def _format_notebook_metadata(notebook):
    """Format notebook metadata section if it exists."""
    if "metadata" not in notebook:
        return []

    return [
        "### Notebook Metadata ###",
        json.dumps(notebook["metadata"], indent=2),
        "",
    ]


def _format_single_output(output):
    """Format a single output cell and return its string representation."""
    if "text" in output:
        return "".join(output["text"])
    if "data" in output:
        if "text/plain" in output["data"]:
            return "".join(output["data"]["text/plain"])
        return f"[Output type: {list(output['data'].keys())}]"
    return ""


def _format_cell_outputs(outputs):
    """Format outputs for a code cell."""
    if not outputs:
        return []

    result = ["-" * 40, "# Outputs:"]

    for output in outputs:
        formatted_output = _format_single_output(output)
        if formatted_output:
            result.append(formatted_output)

    return result


def _process_cell(cell, cell_num):
    """Process a single notebook cell and return its text representation."""
    result = [
        "#" * 80,
        f"# Cell {cell_num} [{cell['cell_type']}]",
        "#" * 80,
    ]

    # Add cell source
    if cell["source"]:
        result.append("".join(cell["source"]))

    # Add cell outputs for code cells
    if cell["cell_type"] == "code" and "outputs" in cell:
        result.extend(_format_cell_outputs(cell["outputs"]))

    # Add empty line after cell
    result.append("\n")

    return result


def convert_notebook_custom(ipynb_path):
    """Convert notebook to text format using custom implementation."""
    notebook = _load_notebook(ipynb_path)

    text_content = ["""> This is automatically generated representation of the Jupyter Notebook. This is read-only format."""]

    # Add metadata if exists
    text_content.extend(_format_notebook_metadata(notebook))

    # Process each cell
    for cell_num, cell in enumerate(notebook["cells"], 1):
        text_content.extend(_process_cell(cell, cell_num))

    return "\n".join(text_content)
