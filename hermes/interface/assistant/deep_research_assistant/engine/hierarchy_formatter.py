from typing import List, Optional

from .file_system import Node
from .xml_formatter import XMLFormatter


class HierarchyFormatter:
    """
    Responsible for formatting problem hierarchies in a consistent XML-like format.
    This class isolates the formatting logic for problem hierarchies.
    """
    
    def __init__(self):
        """Initialize the formatter with an XMLFormatter instance"""
        self.xml_formatter = XMLFormatter(indent_size=2)

    def format_subproblems(self, node: Node) -> str:
        """Format subproblems of a node in XML-like format"""
        if not node.subproblems:
            return "No subproblems defined yet."

        result = []
        
        for title, subproblem in node.subproblems.items():
            # Format node information
            artifacts_count = len(subproblem.artifacts)
            criteria_met = subproblem.get_criteria_met_count()
            criteria_total = subproblem.get_criteria_total_count()
            node_status = subproblem.status.value
            
            # Create attributes dictionary
            attributes = {
                'status': node_status,
                'criteriaProgress': f"{criteria_met}/{criteria_total}",
                'depth': subproblem.depth_from_root,
                'artifacts': artifacts_count
            }
            
            # Always include problem definition regardless of criteria
            content_parts = []
            
            # Add problem definition
            problem_def_content = self.xml_formatter.format_with_attributes(
                "problem_definition", 
                f"  {subproblem.problem_definition}", 
                indent_level=1
            )
            content_parts.append(problem_def_content)
            
            # Add criteria if any
            if subproblem.criteria:
                criteria_items = []
                for i, (criterion, done) in enumerate(
                    zip(subproblem.criteria, subproblem.criteria_done)
                ):
                    status = "✓" if done else "□"
                    criterion_item = self.xml_formatter.format_with_attributes(
                        "criterion", 
                        criterion, 
                        {"status": status},
                        indent_level=2
                    )
                    criteria_items.append(criterion_item)
                
                criteria_content = self.xml_formatter.format_with_attributes(
                    "criteria", 
                    "\n".join(criteria_items), 
                    indent_level=1
                )
                content_parts.append(criteria_content)
            
            # Format the complete subproblem with its content
            formatted_subproblem = self.xml_formatter.format_with_attributes(
                f'"{title}"', 
                "\n".join(content_parts) if content_parts else None,
                attributes
            )
            result.append(formatted_subproblem)
                
        return "\n".join(result)

    def format_problem_path_hierarchy(self, node: Node) -> str:
        """
        Format the hierarchical path from root to the current node in XML-like format.
        Shows the nested structure of problems along the path.
        """
        if not node:
            return "No problem hierarchy available"

        chain = self._get_parent_chain(node)
        if len(chain) <= 1:
            return "No problem hierarchy available"

        # Start with the root node
        current_content = self._format_node_in_path_hierarchy(chain, 0, len(chain)-1)
        
        # Wrap the entire hierarchy in a root tag
        return self.xml_formatter.format_with_attributes(
            "problem_path_hierarchy", 
            current_content
        )
    
    def _format_node_in_path_hierarchy(self, chain: List[Node], current_index: int, target_depth: int) -> str:
        """
        Recursively format a node and its children in the path hierarchy.
        
        Args:
            chain: The list of nodes from root to current
            current_index: The index of the current node in the chain
            target_depth: The depth of the target node (to know when to stop)
            
        Returns:
            Formatted XML-like string for this node and its relevant children
        """
        if current_index > target_depth:
            return ""
            
        current_node = chain[current_index]
        
        # Format node information
        artifacts_count = len(current_node.artifacts)
        criteria_met = current_node.get_criteria_met_count()
        criteria_total = current_node.get_criteria_total_count()
        node_status = current_node.status.value
        
        # Create attributes dictionary
        attributes = {
            'title': current_node.title,
            'status': node_status,
            'criteriaProgress': f"{criteria_met}/{criteria_total}",
            'depth': current_node.depth_from_root,
            'artifacts': artifacts_count
        }
        
        content_parts = []
        
        # Add problem definition
        problem_def_content = self.xml_formatter.format_with_attributes(
            "problem_definition", 
            f"  {current_node.problem_definition}", 
            indent_level=1
        )
        content_parts.append(problem_def_content)
        
        # If we're not at the last node in the chain, add the next node in the path
        if current_index < target_depth:
            # Find the next node in the chain
            next_node = chain[current_index + 1]
            
            # Format all subproblems of the current node, highlighting the one in our path
            subproblems_items = []
            
            for title, subproblem in current_node.subproblems.items():
                # Check if this subproblem is in our path
                is_in_path = (subproblem == next_node)
                
                if is_in_path:
                    # If this subproblem is in our path, recursively format it
                    child_content = self._format_node_in_path_hierarchy(chain, current_index + 1, target_depth)
                    subproblems_items.append(child_content)
                else:
                    # Otherwise, just add a simple reference
                    sub_status = subproblem.status.value
                    subproblem_item = self.xml_formatter.format_with_attributes(
                        "subproblem", 
                        None, 
                        {"title": title, "status": sub_status, "inPath": "false"},
                        indent_level=1
                    )
                    subproblems_items.append(subproblem_item)
            
            if subproblems_items:
                content_parts.append("\n".join(subproblems_items))
        
        # Format the complete node with its content
        node_tag = f'node depth="{current_node.depth_from_root}"'
        return self.xml_formatter.format_with_attributes(
            node_tag, 
            "\n".join(content_parts),
            attributes
        )
    
    def _get_parent_chain(self, node: Node) -> List[Node]:
        """Get the parent chain including the given node"""
        chain = []
        current = node
        while current:
            chain.append(current)
            current = current.parent
        return list(reversed(chain))
