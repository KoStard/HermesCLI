import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
import re

class DeepResearchInterface:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.current_problem_path = self.root_dir
        self.problem_hierarchy = []
        self.load_or_initialize_structure()
        
    def load_or_initialize_structure(self):
        """Load existing structure or initialize a new one"""
        if not self.root_dir.exists():
            self.root_dir.mkdir(parents=True, exist_ok=True)
            
        # Initialize problem hierarchy
        self.problem_hierarchy = self._build_problem_hierarchy()
        
        # If no problem definition exists, create one
        if not (self.current_problem_path / "Problem Definition.md").exists():
            with open(self.current_problem_path / "Problem Definition.md", "w") as f:
                f.write("# Problem Definition\n\nDefine your problem here.")
                
        # Initialize criteria file if it doesn't exist
        if not (self.current_problem_path / "Criteria of Definition of Done.md").exists():
            with open(self.current_problem_path / "Criteria of Definition of Done.md", "w") as f:
                f.write("# Criteria of Definition of Done\n\n")
                
        # Create attachments directory if it doesn't exist
        attachments_dir = self.current_problem_path / "Attachments"
        if not attachments_dir.exists():
            attachments_dir.mkdir(exist_ok=True)
            
        # Create subproblems directory if it doesn't exist
        subproblems_dir = self.current_problem_path / "Subproblems"
        if not subproblems_dir.exists():
            subproblems_dir.mkdir(exist_ok=True)
        
        self.problem_hierarchy = self._build_problem_hierarchy()
    
    def _build_problem_hierarchy(self) -> List[Dict[str, Any]]:
        """Build the problem hierarchy from the file system"""
        hierarchy = []
        current_path = self.current_problem_path
        root_path = self.root_dir
        
        # Build hierarchy from current problem up to root
        while current_path >= root_path:
            problem_def_path = current_path / "Problem Definition.md"
            criteria_path = current_path / "Criteria of Definition of Done.md"
            
            if problem_def_path.exists():
                with open(problem_def_path, "r") as f:
                    problem_def = f.read()
                
                title = current_path.name
                
                criteria_met = 0
                total_criteria = 0
                if criteria_path.exists():
                    with open(criteria_path, "r") as f:
                        criteria_content = f.read()
                        # Count criteria and which are marked as done
                        criteria_lines = [line for line in criteria_content.split("\n") 
                                         if line.strip() and line.strip().startswith("- ")]
                        total_criteria = len(criteria_lines)
                        criteria_met = sum(1 for line in criteria_lines if "[✓]" in line)
                
                hierarchy.insert(0, {
                    "title": title,
                    "path": current_path,
                    "criteria_met": criteria_met,
                    "total_criteria": total_criteria
                })
            
            # If we're at the root, break
            if current_path == root_path:
                break
                
            # Move up to parent
            current_path = current_path.parent
            if current_path.name != "Subproblems":
                # If parent is not a Subproblems directory, we're done
                break
            current_path = current_path.parent  # Move up again to get to the actual parent problem
        
        return hierarchy
    
    def get_problem_definition(self) -> str:
        """Get the current problem definition"""
        problem_def_path = self.current_problem_path / "Problem Definition.md"
        if problem_def_path.exists():
            with open(problem_def_path, "r") as f:
                content = f.read()
                # Remove the title if it exists
                lines = content.split("\n")
                if lines and lines[0].startswith("# "):
                    content = "\n".join(lines[1:]).strip()
                return content
        return ""
    
    def get_criteria(self) -> List[str]:
        """Get the criteria for definition of done"""
        criteria_path = self.current_problem_path / "Criteria of Definition of Done.md"
        criteria = []
        if criteria_path.exists():
            with open(criteria_path, "r") as f:
                content = f.read()
                lines = content.split("\n")
                for line in lines:
                    if line.strip() and line.strip().startswith("- "):
                        criteria.append(line.strip())
        return criteria
    
    def get_breakdown_structure(self) -> Dict[str, str]:
        """Get the breakdown structure (subproblems)"""
        subproblems_dir = self.current_problem_path / "Subproblems"
        breakdown = {}
        
        if subproblems_dir.exists():
            for subproblem_dir in subproblems_dir.iterdir():
                if subproblem_dir.is_dir():
                    problem_def_path = subproblem_dir / "Problem Definition.md"
                    if problem_def_path.exists():
                        with open(problem_def_path, "r") as f:
                            content = f.read()
                            # Remove the title if it exists
                            lines = content.split("\n")
                            if lines and lines[0].startswith("# "):
                                content = "\n".join(lines[1:]).strip()
                            breakdown[subproblem_dir.name] = content
        
        return breakdown
    
    def get_attachments(self) -> Dict[str, str]:
        """Get all attachments for the current problem"""
        attachments_dir = self.current_problem_path / "Attachments"
        attachments = {}
        
        if attachments_dir.exists():
            for attachment_file in attachments_dir.iterdir():
                if attachment_file.is_file():
                    with open(attachment_file, "r") as f:
                        attachments[attachment_file.name] = f.read()
        
        return attachments
    
    def get_parent_chain(self) -> List[Dict[str, Any]]:
        """Get the parent chain information"""
        parent_chain = []
        
        for i, problem in enumerate(self.problem_hierarchy[:-1]):  # Exclude current problem
            problem_path = problem["path"]
            
            # Get problem definition
            problem_def_path = problem_path / "Problem Definition.md"
            problem_def = ""
            if problem_def_path.exists():
                with open(problem_def_path, "r") as f:
                    content = f.read()
                    lines = content.split("\n")
                    if lines and lines[0].startswith("# "):
                        content = "\n".join(lines[1:]).strip()
                    problem_def = content
            
            # Get breakdown structure
            breakdown = {}
            subproblems_dir = problem_path / "Subproblems"
            if subproblems_dir.exists():
                for subproblem_dir in subproblems_dir.iterdir():
                    if subproblem_dir.is_dir():
                        sub_def_path = subproblem_dir / "Problem Definition.md"
                        if sub_def_path.exists():
                            with open(sub_def_path, "r") as f:
                                content = f.read()
                                lines = content.split("\n")
                                if lines and lines[0].startswith("# "):
                                    content = "\n".join(lines[1:]).strip()
                                breakdown[subproblem_dir.name] = content
            
            parent_chain.append({
                "level": i,
                "title": problem["title"],
                "definition": problem_def,
                "breakdown": breakdown
            })
        
        return parent_chain
    
    def add_criteria(self, criteria_text: str):
        """Add a new criteria to the definition of done"""
        criteria_path = self.current_problem_path / "Criteria of Definition of Done.md"
        
        existing_content = ""
        if criteria_path.exists():
            with open(criteria_path, "r") as f:
                existing_content = f.read()
        
        # If file is empty or doesn't have a title, add one
        if not existing_content or not existing_content.strip():
            existing_content = "# Criteria of Definition of Done\n\n"
        
        # Add the new criteria
        with open(criteria_path, "w") as f:
            # Count existing criteria to determine the next index
            criteria_count = len([line for line in existing_content.split("\n") 
                               if line.strip() and line.strip().startswith("- ")])
            
            new_criteria = f"- [ ] {criteria_text}"
            
            if existing_content.strip().endswith("\n"):
                f.write(f"{existing_content}{new_criteria}\n")
            else:
                f.write(f"{existing_content}\n{new_criteria}\n")
        
        # Update the problem hierarchy
        self.problem_hierarchy = self._build_problem_hierarchy()
    
    def mark_criteria_as_done(self, criteria_index: int):
        """Mark a criteria as done by its index"""
        criteria_path = self.current_problem_path / "Criteria of Definition of Done.md"
        
        if not criteria_path.exists():
            return
        
        with open(criteria_path, "r") as f:
            lines = f.readlines()
        
        # Find criteria lines
        criteria_lines = []
        for i, line in enumerate(lines):
            if line.strip() and line.strip().startswith("- "):
                criteria_lines.append(i)
        
        # Check if index is valid
        if 0 <= criteria_index < len(criteria_lines):
            line_index = criteria_lines[criteria_index]
            line = lines[line_index]
            
            # Replace [ ] with [✓]
            if "[ ]" in line:
                lines[line_index] = line.replace("[ ]", "[✓]")
            
            # Write back to file
            with open(criteria_path, "w") as f:
                f.writelines(lines)
        
        # Update the problem hierarchy
        self.problem_hierarchy = self._build_problem_hierarchy()
    
    def add_subproblem(self, title: str, content: str):
        """Add a new subproblem"""
        subproblems_dir = self.current_problem_path / "Subproblems"
        if not subproblems_dir.exists():
            subproblems_dir.mkdir(exist_ok=True)
        
        # Create directory for the subproblem
        subproblem_dir = subproblems_dir / title
        if not subproblem_dir.exists():
            subproblem_dir.mkdir(exist_ok=True)
        
        # Create problem definition file
        with open(subproblem_dir / "Problem Definition.md", "w") as f:
            f.write(f"# {title}\n\n{content}")
        
        # Create criteria file
        with open(subproblem_dir / "Criteria of Definition of Done.md", "w") as f:
            f.write("# Criteria of Definition of Done\n\n")
        
        # Create attachments directory
        attachments_dir = subproblem_dir / "Attachments"
        if not attachments_dir.exists():
            attachments_dir.mkdir(exist_ok=True)
        
        # Create subproblems directory
        sub_subproblems_dir = subproblem_dir / "Subproblems"
        if not sub_subproblems_dir.exists():
            sub_subproblems_dir.mkdir(exist_ok=True)
        
        # Update breakdown structure
        self._update_breakdown_structure()
    
    def _update_breakdown_structure(self):
        """Update the breakdown structure file based on subproblems"""
        breakdown_path = self.current_problem_path / "Breakdown Structure.md"
        subproblems = self.get_breakdown_structure()
        
        with open(breakdown_path, "w") as f:
            f.write("# Breakdown Structure\n\n")
            for title, content in subproblems.items():
                f.write(f"### {title}\n{content}\n\n")
    
    def add_attachment(self, name: str, content: str):
        """Add a new attachment"""
        attachments_dir = self.current_problem_path / "Attachments"
        if not attachments_dir.exists():
            attachments_dir.mkdir(exist_ok=True)
        
        with open(attachments_dir / name, "w") as f:
            f.write(content)
    
    def write_report(self, content: str):
        """Write the 3-page report"""
        report_path = self.current_problem_path / "Report 3 Pager.md"
        
        with open(report_path, "w") as f:
            f.write(content)
    
    def append_to_problem_definition(self, content: str):
        """Append content to the problem definition"""
        problem_def_path = self.current_problem_path / "Problem Definition.md"
        
        existing_content = ""
        if problem_def_path.exists():
            with open(problem_def_path, "r") as f:
                existing_content = f.read()
        
        with open(problem_def_path, "w") as f:
            f.write(f"{existing_content}\n\n{content}")
    
    def focus_down(self, subproblem_title: str):
        """Focus down to a subproblem"""
        subproblem_path = self.current_problem_path / "Subproblems" / subproblem_title
        
        if subproblem_path.exists() and subproblem_path.is_dir():
            self.current_problem_path = subproblem_path
            self.problem_hierarchy = self._build_problem_hierarchy()
            return True
        return False
    
    def focus_up(self):
        """Focus up to the parent problem"""
        if len(self.problem_hierarchy) > 1:  # If we're not at the root
            parent_path = self.current_problem_path.parent.parent  # Go up two levels (Subproblems/parent)
            if parent_path.exists() and parent_path.is_dir():
                self.current_problem_path = parent_path
                self.problem_hierarchy = self._build_problem_hierarchy()
                return True
        return False
    
    def render_interface(self) -> str:
        """Render the full interface"""
        output = []
        
        # Header
        output.append("# Deep Research Interface")
        output.append("")
        output.append("You are in deep research mode. Use commands to structure your investigation.")
        output.append("")
        
        # Simple Commands
        output.append("## Simple Commands")
        output.append("- ///add_criteria Your criteria text here")
        output.append("- ///mark_criteria_as_done criteria_index")
        output.append("- ///focus_down Subproblem Title")
        output.append("- ///focus_up")
        output.append("")
        
        # Block Commands
        output.append("## Block Commands")
        output.append("```")
        output.append("<<<<< add_subproblem")
        output.append("///title")
        output.append("Subproblem Title")
        output.append("///content")
        output.append("Problem definition goes here")
        output.append(">>>>>")
        output.append("```")
        output.append("")
        
        output.append("```")
        output.append("<<<<< add_attachment")
        output.append("///name")
        output.append("attachment_name.txt")
        output.append("///content")
        output.append("Content goes here")
        output.append(">>>>>")
        output.append("```")
        output.append("")
        
        output.append("```")
        output.append("<<<<< write_report")
        output.append("///content")
        output.append("Report content goes here")
        output.append(">>>>>")
        output.append("```")
        output.append("")
        
        output.append("```")
        output.append("<<<<< append_to_problem_definition")
        output.append("///content")
        output.append("Content to append to the problem definition.")
        output.append(">>>>>")
        output.append("```")
        output.append("")
        
        # Attachments
        output.append("======================")
        output.append("# Attachments Of Current Problem")
        output.append("")
        output.append("<attachments>")
        
        attachments = self.get_attachments()
        for name, content in attachments.items():
            output.append(f"<attachment name=\"{name}\">")
            output.append(content)
            output.append("</attachment>")
            output.append("")
        
        if not attachments:
            output.append("No attachments for this problem.")
        
        output.append("</attachments>")
        output.append("")
        
        # Current Problem
        output.append("======================")
        current_title = self.problem_hierarchy[-1]["title"] if self.problem_hierarchy else "Root Problem"
        output.append(f"# Current Problem: {current_title}")
        output.append("")
        
        # Problem Hierarchy
        output.append("## Problem Hierarchy")
        
        if self.problem_hierarchy:
            # Format the hierarchy as a tree
            hierarchy_lines = []
            for i, problem in enumerate(self.problem_hierarchy):
                prefix = " " * (i * 4) + ("└── " if i > 0 else "")
                if i == len(self.problem_hierarchy) - 1:  # Current problem
                    hierarchy_lines.append(f"{prefix}CURRENT: {problem['title']}")
                else:
                    criteria_info = ""
                    if problem["total_criteria"] > 0:
                        criteria_info = f" [{problem['criteria_met']}/{problem['total_criteria']} criteria met]"
                    
                    if i == 0:
                        hierarchy_lines.append(f"{prefix}Root: {problem['title']}{criteria_info}")
                    else:
                        hierarchy_lines.append(f"{prefix}Level {i}: {problem['title']}{criteria_info}")
            
            # Format the tree with proper indentation
            tree_output = []
            for i, line in enumerate(hierarchy_lines):
                if i < len(hierarchy_lines) - 1:
                    tree_output.append(line)
                    tree_output.append(" " * (4 * i) + "    └── ")
                else:
                    tree_output.append(line)
            
            output.extend(tree_output)
        else:
            output.append(" └── Root Problem")
        
        output.append("")
        
        # Problem Definition
        output.append("## Problem Definition")
        problem_def = self.get_problem_definition()
        output.append(problem_def if problem_def else "No problem definition available.")
        output.append("")
        
        # Criteria
        output.append("## Criteria of Definition of Done")
        criteria = self.get_criteria()
        if criteria:
            for i, criterion in enumerate(criteria):
                output.append(f"{i}. {criterion}")
        else:
            output.append("No criteria defined yet.")
        output.append("")
        
        # Breakdown Structure
        output.append("## Breakdown Structure")
        breakdown = self.get_breakdown_structure()
        if breakdown:
            for title, content in breakdown.items():
                output.append(f"### {title}")
                output.append(content)
                output.append("")
        else:
            output.append("No subproblems defined yet.")
        output.append("")
        
        # Parent Chain
        output.append("## Parent chain")
        parent_chain = self.get_parent_chain()
        if parent_chain:
            for parent in parent_chain:
                level = parent["level"]
                title = parent["title"]
                definition = parent["definition"]
                
                output.append(f"### L{level} {'Root ' if level == 0 else ''}Problem: {title}")
                output.append(definition)
                output.append("")
                
                output.append(f"#### L{level} Problem Breakdown Structure")
                for sub_title, sub_def in parent["breakdown"].items():
                    output.append(f"##### {sub_title}")
                    output.append(sub_def)
                    output.append("")
        else:
            output.append("No parent problems.")
        output.append("")
        
        # Goal
        output.append("## Goal")
        output.append(f"Your task is to continue investigating the current problem on {current_title}. Add criteria if needed, create subproblems to structure your investigation, and work toward producing a comprehensive 3-page report. Use the attachments for reference and add new ones as needed. When ready to move to a different focus area, use the focus commands.")
        
        return "\n".join(output)

def parse_command(text: str):
    """Parse commands from the assistant's response"""
    # Parse simple commands
    simple_command_pattern = r"///(\w+)(?:\s+(.+))?"
    simple_matches = re.findall(simple_command_pattern, text)
    
    commands = []
    for command, args in simple_matches:
        commands.append({
            "type": command,
            "args": args.strip() if args else ""
        })
    
    # Parse block commands
    block_pattern = r"<<<<< (\w+)\n(.*?)\n>>>>>"
    block_matches = re.findall(block_pattern, text, re.DOTALL)
    
    for command, content in block_matches:
        args = {}
        # Parse sections within the block
        section_pattern = r"///(\w+)\n(.*?)(?=///\w+|\Z)"
        section_matches = re.findall(section_pattern, content, re.DOTALL)
        
        for section_name, section_content in section_matches:
            args[section_name] = section_content.strip()
        
        commands.append({
            "type": command,
            "args": args
        })
    
    return commands

def execute_commands(interface: DeepResearchInterface, commands: List[Dict]):
    """Execute the parsed commands"""
    for command in commands:
        cmd_type = command["type"]
        args = command["args"]
        
        if cmd_type == "add_criteria":
            interface.add_criteria(args)
            print(f"Added criteria: {args}")
        
        elif cmd_type == "mark_criteria_as_done":
            try:
                index = int(args)
                interface.mark_criteria_as_done(index)
                print(f"Marked criteria {index} as done")
            except ValueError:
                print(f"Invalid criteria index: {args}")
        
        elif cmd_type == "focus_down":
            success = interface.focus_down(args)
            if success:
                print(f"Focused down to: {args}")
            else:
                print(f"Could not focus down to: {args}")
        
        elif cmd_type == "focus_up":
            success = interface.focus_up()
            if success:
                print("Focused up to parent problem")
            else:
                print("Already at root problem, cannot focus up")
        
        elif cmd_type == "add_subproblem":
            if isinstance(args, dict) and "title" in args and "content" in args:
                interface.add_subproblem(args["title"], args["content"])
                print(f"Added subproblem: {args['title']}")
            else:
                print("Missing title or content for add_subproblem")
        
        elif cmd_type == "add_attachment":
            if isinstance(args, dict) and "name" in args and "content" in args:
                interface.add_attachment(args["name"], args["content"])
                print(f"Added attachment: {args['name']}")
            else:
                print("Missing name or content for add_attachment")
        
        elif cmd_type == "write_report":
            if isinstance(args, dict) and "content" in args:
                interface.write_report(args["content"])
                print("Wrote 3-page report")
            else:
                print("Missing content for write_report")
        
        elif cmd_type == "append_to_problem_definition":
            if isinstance(args, dict) and "content" in args:
                interface.append_to_problem_definition(args["content"])
                print("Appended to problem definition")
            else:
                print("Missing content for append_to_problem_definition")
        
        else:
            print(f"Unknown command: {cmd_type}")

def main():
    # Check if a root directory was provided
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = "research_project"
    
    # Initialize the interface
    interface = DeepResearchInterface(root_dir)
    
    print("Deep Research Mock Interface")
    print("===========================")
    print("You are playing the role of the assistant.")
    print("Type your response and press Escape + Enter to submit.")
    print("Commands will be automatically executed.")
    print("Type 'exit' to quit.")
    print()
    
    # Display the initial interface
    print(interface.render_interface())
    print("\n--- Your response (Esc+Enter to submit) ---")
    
    # Main interaction loop
    while True:
        # Collect multiline input until Escape+Enter
        lines = []
        while True:
            try:
                line = input()
                if line.lower() == "exit":
                    print("Exiting...")
                    return
                lines.append(line)
            except EOFError:  # This will be triggered by Escape+Enter in some terminals
                break
        
        # Join the lines to form the complete response
        response = "\n".join(lines)
        
        # Parse and execute commands
        commands = parse_command(response)
        if commands:
            execute_commands(interface, commands)
        else:
            print("\nNo commands detected. Continuing investigation...")
        
        # Display the updated interface
        print("\n" + interface.render_interface())
        print("\n--- Your response (Esc+Enter to submit) ---")

if __name__ == "__main__":
    main()
