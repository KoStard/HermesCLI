from typing import Dict, List, Any, Optional


class XMLFormatter:
    """
    Utility class for formatting Python objects into XML-like text representation.
    Handles proper indentation for nested structures and provides a consistent API.
    """
    
    def __init__(self, indent_size: int = 2):
        """
        Initialize the formatter with specified indentation size.
        
        Args:
            indent_size: Number of spaces to use for each indentation level
        """
        self.indent_size = indent_size
    
    def format(self, obj: Any, root_tag: Optional[str] = None, indent_level: int = 0) -> str:
        """
        Format any Python object into an XML-like string representation.
        
        Args:
            obj: The object to format (dict, list, str, etc.)
            root_tag: Optional root tag name to wrap the object
            indent_level: Current indentation level
            
        Returns:
            Formatted XML-like string
        """
        if root_tag is not None:
            result = []
            indent = " " * (indent_level * self.indent_size)
            result.append(f"{indent}<{root_tag}>")
            formatted_content = self.format(obj, None, indent_level + 1)
            result.append(formatted_content)
            result.append(f"{indent}</{root_tag}>")
            return "\n".join(result)
        
        if obj is None:
            return f"{' ' * (indent_level * self.indent_size)}None"
        
        if isinstance(obj, dict):
            return self._format_dict(obj, indent_level)
        elif isinstance(obj, list):
            return self._format_list(obj, indent_level)
        else:
            # For simple types, just convert to string with proper indentation
            indent = " " * (indent_level * self.indent_size)
            return f"{indent}{str(obj)}"
    
    def _format_dict(self, obj: Dict, indent_level: int) -> str:
        """Format a dictionary into XML-like representation"""
        if not obj:
            indent = " " * (indent_level * self.indent_size)
            return f"{indent}Empty"
            
        result = []
        for key, value in obj.items():
            indent = " " * (indent_level * self.indent_size)
            
            # Handle different value types
            if isinstance(value, dict) and value:
                # For non-empty dictionaries, create a tag with nested content
                result.append(f"{indent}<{key}>")
                result.append(self._format_dict(value, indent_level + 1))
                result.append(f"{indent}</{key}>")
            elif isinstance(value, list) and value:
                # For non-empty lists, create a tag with nested items
                result.append(f"{indent}<{key}>")
                result.append(self._format_list(value, indent_level + 1))
                result.append(f"{indent}</{key}>")
            else:
                # For simple values or empty collections, use self-closing tag with attributes
                if isinstance(value, (str, int, float, bool)) or value is None:
                    # Format simple values as attributes
                    attr_value = str(value).replace('"', '\\"') if value is not None else "null"
                    result.append(f'{indent}<{key} value="{attr_value}" />')
                else:
                    # Empty collections
                    result.append(f"{indent}<{key} empty=\"true\" />")
                    
        return "\n".join(result)
    
    def _format_list(self, obj: List, indent_level: int) -> str:
        """Format a list into XML-like representation"""
        if not obj:
            indent = " " * (indent_level * self.indent_size)
            return f"{indent}Empty list"
            
        result = []
        for i, item in enumerate(obj):
            indent = " " * (indent_level * self.indent_size)
            
            # Use 'item' as the tag name for list elements
            if isinstance(item, dict) and item:
                # For dictionaries in a list, use item_N as tag and add attributes
                result.append(f"{indent}<item_{i}>")
                result.append(self._format_dict(item, indent_level + 1))
                result.append(f"{indent}</item_{i}>")
            elif isinstance(item, list) and item:
                # For nested lists
                result.append(f"{indent}<item_{i}>")
                result.append(self._format_list(item, indent_level + 1))
                result.append(f"{indent}</item_{i}>")
            else:
                # For simple values
                if isinstance(item, (str, int, float, bool)) or item is None:
                    item_str = str(item).replace('"', '\\"') if item is not None else "null"
                    result.append(f'{indent}<item value="{item_str}" />')
                else:
                    # Empty collections
                    result.append(f"{indent}<item empty=\"true\" />")
                    
        return "\n".join(result)
    
    def format_with_attributes(self, tag: str, content: Optional[str] = None, 
                              attributes: Optional[Dict[str, Any]] = None,
                              indent_level: int = 0) -> str:
        """
        Format a tag with attributes and optional content.
        
        Args:
            tag: The tag name
            content: Optional content inside the tag
            attributes: Optional dictionary of attributes
            indent_level: Current indentation level
            
        Returns:
            Formatted XML-like string
        """
        indent = " " * (indent_level * self.indent_size)
        attrs_str = ""
        
        # Format attributes if any
        if attributes:
            for key, value in attributes.items():
                value_str = str(value).replace('"', '\\"')
                attrs_str += f' {key}="{value_str}"'
        
        # Self-closing tag if no content
        if content is None:
            return f"{indent}<{tag}{attrs_str} />"
        
        # Tag with content
        return f"{indent}<{tag}{attrs_str}>\n{content}\n{indent}</{tag}>"
