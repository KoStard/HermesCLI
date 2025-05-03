import os
from pathlib import Path
from typing import List


class FuzzyFilesSelector:
    def __init__(self):
        pass

    def select_files(self, multi=True):
        """
        Select files using fuzzy finder.
        Behaviour like fzf, getting from current working directory child files, recursively through the files, excluding files starting with a dot.
        Return should be a list of absolute paths for the selected files.
        Empty list is selection as well.
        """
        # Get all files recursively from current directory
        choices = self._get_file_choices()

        # If no files found
        if not choices:
            return []

        # Configure the fuzzy selection prompt
        questions = [
            {
                "type": "fuzzy",
                "name": "files",
                "message": "Select files:" if multi else "Select a file:",
                "choices": choices,
                "multiselect": multi,
                "filter": lambda result: [item for item in result if item is not None]
                if multi
                else [result],
                "validate": lambda result: True,
                "transformer": lambda result: f"{len(result)} files selected"
                if multi and result
                else "No files selected",
                "long_instruction": "Use arrow keys to navigate, tab to select, enter to confirm, Ctrl+c to cancel selection",
                "mandatory": False,
                "height": min(15, len(choices) + 2),
            }
        ]

        # Show the prompt and get the selection
        try:
            from InquirerPy import prompt
            result = prompt(questions)

            # Return the selected files as absolute paths
            if not result["files"]:
                return []
        except KeyboardInterrupt:
            # Handle escape key (KeyboardInterrupt)
            return []

        return [str(Path(file).absolute()) for file in result["files"]]

    def _get_file_choices(self) -> List[str]:
        """Get all files recursively from current directory, excluding hidden files."""
        choices = []

        for root, dirs, files in os.walk("."):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            # Add non-hidden files
            for file in files:
                if not file.startswith("."):
                    file_path = os.path.join(root, file)
                    choices.append(file_path)

        return sorted(choices)


if __name__ == "__main__":
    selector = FuzzyFilesSelector()
    selected_files = selector.select_files()
    print("Selected files:", selected_files)
