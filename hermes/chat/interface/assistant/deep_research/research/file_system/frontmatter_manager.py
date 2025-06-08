class FrontmatterManager:
    def extract_frontmatter(self, full_content: str) -> tuple[dict, str]:
        """Provided with the full content of the markdown file, extract the front-matter into a dict and return the rest of the content.

        Frontmatter is expected to be at the beginning of the file, enclosed between triple-dash lines (---).

        Args:
            full_content: The complete content of the markdown file

        Returns:
            A tuple containing:
            - A dictionary of the parsed frontmatter (empty if none found)
            - The remaining content of the file (without the frontmatter)
        """
        import yaml

        # Default return values
        frontmatter = {}
        content = full_content

        # Check if the content starts with frontmatter delimiter
        if full_content.startswith("---\n"):
            # Find the closing delimiter
            end_delimiter_pos = full_content.find("\n---", 4)

            if end_delimiter_pos != -1:
                # Extract the frontmatter section
                frontmatter_text = full_content[4:end_delimiter_pos]

                try:
                    # Parse the YAML frontmatter
                    frontmatter = yaml.safe_load(frontmatter_text) or {}

                    # Extract the content after the frontmatter
                    content = full_content[end_delimiter_pos + 4 :].lstrip()
                except yaml.YAMLError:
                    # If YAML parsing fails, return empty frontmatter and original content
                    pass

        return frontmatter, content

    def add_frontmatter(self, content: str, metadata: dict) -> str:
        """Given with the future content of the markdown file and the metadata for it,
        add the metadata as a front-matter and return the final content

        Args:
            content: The markdown content without frontmatter
            metadata: Dictionary containing metadata to add as frontmatter

        Returns:
            The content with frontmatter added at the beginning
        """
        import yaml

        # If metadata is empty, return the original content
        if not metadata:
            return content

        # Convert metadata to YAML format
        frontmatter_yaml = yaml.dump(metadata, default_flow_style=False, sort_keys=False)

        # Combine frontmatter with content
        return f"---\n{frontmatter_yaml}---\n\n{content.lstrip()}"
