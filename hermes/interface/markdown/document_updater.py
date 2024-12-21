import os
from datetime import datetime
import shutil
from typing import List
from .header import Header
from .section_path import SectionPath

class MarkdownDocumentUpdater:
    """Handles operations for updating markdown document sections."""
    
    def __init__(self, file_path: str, backup_dir: str = '/tmp/hermes/backups'):
        self.file_path = file_path
        self.backup_dir = backup_dir
        
    def _create_if_not_exists(self, section_path: List[str], content: str) -> None:
        """Create a new markdown file with initial section structure."""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, 'w') as f:
            for i, header in enumerate(section_path, 1):
                f.write('#' * i + ' ' + header + '\n')
            f.write(content)
            
    def _backup_file(self) -> None:
        """Create a backup copy of the file."""
        if not os.path.exists(self.file_path):
            return
            
        os.makedirs(self.backup_dir, exist_ok=True)
        filename = os.path.basename(self.file_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(self.backup_dir, f"{filename}_{timestamp}.bak")
        shutil.copy2(self.file_path, backup_path)
        
    def update_section(self, section_path: List[str], new_content: str, mode: str) -> None:
        """
        Update a section in the markdown document.
        
        Args:
            section_path: List of headers leading to target section
            new_content: Content to update/append
            mode: 'append_markdown_section' or 'update_markdown_section'
        """
        if not os.path.exists(self.file_path):
            self._create_if_not_exists(section_path, new_content)
            return
            
        self._backup_file()
        if not new_content.endswith('\n'):
            new_content += '\n'
        
        with open(self.file_path, 'r') as f:
            lines = f.readlines()
        
        is_preface = False
        if section_path[-1] == '__preface':
            section_path = section_path[:-1]
            is_preface = True

        updated_lines = self._process_lines(lines, section_path, new_content, mode, is_preface)
        
        with open(self.file_path, 'w') as f:
            f.writelines(updated_lines)
            
    def _process_lines(self, lines: List[str], section_path: List[str], 
                      new_content: str, mode: str, is_preface: bool) -> List[str]:
        """Process document lines and apply the update."""
        if mode not in ['append_markdown_section', 'update_markdown_section']:
            raise ValueError(f"Invalid mode: {mode}")
        path_tracker = SectionPath()
        updated_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            header = Header.parse(line)
            
            if header:
                path_tracker.update(header)
                if path_tracker.matches(section_path):
                    if is_preface:
                        start_of_next_section = self._find_start_of_next_section(lines[i+1:]) + 1
                        if mode == 'append_markdown_section':
                            updated_lines.extend(lines[i:i+start_of_next_section])
                            updated_lines.append(new_content)
                        elif mode == 'update_markdown_section':
                            updated_lines.extend([line, new_content])
                        i += start_of_next_section - 1
                    elif mode == 'append_markdown_section':
                        section_end = self._find_section_end(lines[i+1:], header.level) + 1
                        updated_lines.extend(lines[i:i + section_end])
                        updated_lines.append(new_content)
                        i += section_end - 1
                    elif mode == 'update_markdown_section':
                        updated_lines.append(line)
                        updated_lines.append(new_content)
                        i = self._skip_existing_content(lines, i, header.level)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
            i += 1
                
        return updated_lines
        
    def _find_section_end(self, lines: List[str], current_level: int) -> int:
        """Find the end index of current section."""
        for i, line in enumerate(lines):
            header = Header.parse(line)
            if header and header.level <= current_level:
                return i
        return len(lines)

    def _find_start_of_next_section(self, lines: List[str]) -> int:
        """Find the start index of the next section."""
        for i, line in enumerate(lines):
            header = Header.parse(line)
            if header:
                return i
        return len(lines)

        
    def _skip_existing_content(self, lines: List[str], start_idx: int, 
                             current_level: int) -> int:
        """Skip the existing content of a section."""
        i = start_idx + 1
        while i < len(lines):
            header = Header.parse(lines[i])
            if header and header.level <= current_level:
                return i - 1
            i += 1
        return i - 1

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Markdown Document Updater')
    parser.add_argument('file_path', type=str, help='Path to the markdown file')
    args = parser.parse_args()
    updater = MarkdownDocumentUpdater(args.file_path)
    updater.update_section(['T1'], 'New content for Section 1.1', 'update_markdown_section')