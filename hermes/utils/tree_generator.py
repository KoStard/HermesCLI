import os


class TreeGenerator:
    def __init__(self, exclusions: list[callable] = None):
        if exclusions is None:
            exclusions = [lambda x: x.startswith("."), lambda x: x == "__pycache__"]
        self.exclusions = exclusions

    def generate_tree(self, root_path: str, depth: int = None) -> str:
        """
        Generates a text-based tree representation of a directory structure.

        Args:
            root_path: The path to the root directory.
            depth: The maximum depth of the tree. If None, the tree will be generated to full depth.

        Returns:
            A str containing the tree representation.
        """
        return self._build_tree(root_path, "", depth, 0)

    def _build_tree(
        self, current_path: str, prefix: str, depth: int, current_depth: int
    ) -> str:
        """
        Recursively builds the tree string.

        Args:
            current_path: The current path being processed.
            prefix: The prefix for the current level.
            depth: The maximum depth of the tree.
            current_depth: The current depth of the tree.

        Returns:
            The tree string for the current level.
        """
        if depth is not None and current_depth > depth:
            return ""

        try:
            entries = os.listdir(current_path)
        except FileNotFoundError:
            return f"{prefix} [Not Found]\n"

        tree_string = ""

        filtered_entries = [
            entry
            for entry in entries
            if not any(excl(entry) for excl in self.exclusions)
        ]

        for i, entry in enumerate(filtered_entries):
            is_last = i == len(filtered_entries) - 1
            entry_path = os.path.join(current_path, entry)

            if os.path.isdir(entry_path):
                tree_string += f"{prefix}{'-' if not prefix else '--'}{entry}\n"
                new_prefix = prefix + ("  " if is_last else "--")
                tree_string += self._build_tree(
                    entry_path, new_prefix, depth, current_depth + 1
                )
            else:
                tree_string += f"{prefix}{'-' if not prefix else '--'}{entry}\n"

        return tree_string


if __name__ == "__main__":
    generator = TreeGenerator()
    tree_message = generator.generate_tree(".")
    print(tree_message.text)
