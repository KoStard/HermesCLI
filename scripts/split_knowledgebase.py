#!/usr/bin/env python3
"""
Script to migrate knowledge base from old format to new format.

Old format: Single file at Researches/_shared_knowledge_base.md
New format: Individual files under Knowledgebase/{title}.md

Usage: uv run split_knowledgebase path_to_shared_file
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from hermes.chat.interface.assistant.agent_old.framework.research.file_system.markdown_file_with_metadata import (
    MarkdownFileWithMetadataImpl,
)


def parse_old_knowledge_base(content: str) -> list[dict[str, Any]]:
    """Parse the old knowledge base format and extract entries."""
    from hermes.chat.interface.assistant.agent_old.framework.research.file_system.frontmatter_manager import (
        FrontmatterManager,
    )

    entries = []
    frontmatter_manager = FrontmatterManager()

    # Split content by the separator
    sections = content.split("<!-- HERMES_KNOWLEDGE_ENTRY_SEPARATOR -->")

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extract frontmatter and content
        metadata, entry_content = frontmatter_manager.extract_frontmatter(section)

        if not metadata or "title" not in metadata:
            continue

        # Create entry from the extracted metadata and content
        entry = {
            "title": metadata.get("title", "Untitled Entry"),
            "content": entry_content,
            "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
            "author_node_title": metadata.get("author_node_title", "migration_script"),
            "tags": metadata.get("tags", []),
            "source": metadata.get("source"),
            "importance": metadata.get("importance", 1),
            "confidence": metadata.get("confidence", 1),
        }

        entries.append(entry)

    return entries


def save_entry_to_new_format(entry: dict[str, Any], knowledgebase_dir: Path) -> None:
    """Save a single entry to the new format."""
    # Create markdown file with metadata
    file_with_metadata = MarkdownFileWithMetadataImpl(entry["title"], entry["content"])

    # Set all metadata except title and content
    metadata_keys = ["timestamp", "author_node_title", "tags", "source", "importance", "confidence"]
    for key in metadata_keys:
        if key in entry:
            file_with_metadata.set_metadata_key(key, entry[key])

    # Save the file
    file_with_metadata.save_file_in_directory(knowledgebase_dir)


def migrate_knowledge_base(shared_file_path: Path) -> None:
    """Migrate knowledge base from old format to new format."""
    if not shared_file_path.exists():
        print(f"Error: File {shared_file_path} does not exist")
        sys.exit(1)

    if not shared_file_path.is_file():
        print(f"Error: {shared_file_path} is not a file")
        sys.exit(1)

    # Read the old knowledge base file
    try:
        content = shared_file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading file {shared_file_path}: {e}")
        sys.exit(1)

    # Parse entries from old format
    entries = parse_old_knowledge_base(content)

    if not entries:
        print("No knowledge base entries found in the file")
        return

    # Create Knowledgebase directory
    knowledgebase_dir = shared_file_path.parent.parent / "Knowledgebase"
    knowledgebase_dir.mkdir(exist_ok=True)

    # Save each entry to new format
    successful_migrations = 0
    for entry in entries:
        try:
            save_entry_to_new_format(entry, knowledgebase_dir)
            successful_migrations += 1
            print(f"✓ Migrated: {entry['title']}")
        except Exception as e:
            print(f"✗ Failed to migrate '{entry['title']}': {e}")

    print(f"\nMigration completed: {successful_migrations}/{len(entries)} entries migrated successfully")
    print(f"New knowledge base location: {knowledgebase_dir}")


def main():
    """Main entry point for the script."""
    if len(sys.argv) != 2:
        print("Usage: uv run split_knowledgebase path_to_shared_file")
        sys.exit(1)

    shared_file_path = Path(sys.argv[1]).expanduser().resolve()
    migrate_knowledge_base(shared_file_path)


if __name__ == "__main__":
    main()
