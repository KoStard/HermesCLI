import json


def convert_notebook_custom(ipynb_path):
    """Convert notebook to text format using custom implementation."""
    with open(ipynb_path, "r", encoding="utf-8") as f:
        notebook = json.load(f)

    text_content = [
        """> This is automatically generated representation of the Jupyter Notebook. This is read-only format."""
    ]

    # Add notebook metadata if exists
    if "metadata" in notebook:
        text_content.append("### Notebook Metadata ###")
        text_content.append(json.dumps(notebook["metadata"], indent=2))
        text_content.append("")

    for cell_num, cell in enumerate(notebook["cells"], 1):
        # Cell separator
        text_content.append("#" * 80)
        text_content.append(f'# Cell {cell_num} [{cell["cell_type"]}]')
        text_content.append("#" * 80)

        # Cell source
        if cell["source"]:
            source = "".join(cell["source"])
            text_content.append(source)

        # Cell outputs (for code cells)
        if cell["cell_type"] == "code" and "outputs" in cell and cell["outputs"]:
            text_content.append("-" * 40)
            text_content.append("# Outputs:")
            for output in cell["outputs"]:
                if "text" in output:
                    text_content.append("".join(output["text"]))
                elif "data" in output:
                    if "text/plain" in output["data"]:
                        text_content.append("".join(output["data"]["text/plain"]))
                    # Handle other output types like images, HTML, etc.
                    else:
                        text_content.append(
                            f'[Output type: {list(output["data"].keys())}]'
                        )

        text_content.append("\n")  # Add extra newline between cells

    return "\n".join(text_content)
