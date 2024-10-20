import xml.etree.ElementTree as ET
from typing import Optional
from .base import PromptBuilder
from hermes.file_processors.base import FileProcessor
from ..registry import register_prompt_builder
import textwrap

@register_prompt_builder("xml")
class XMLPromptBuilder(PromptBuilder):
    def __init__(self, file_processor: FileProcessor, author: str, do_introduction: bool = False):
        self.file_processor = file_processor
        self.author = author
        self.do_introduction = do_introduction
        self.root = None
        self.input_elem = None
        self.erase()

    def add_text(self, text: str, name: Optional[str] = None):
        if name:
            text_elem = ET.SubElement(self.input_elem, "text", name=name)
        else:
            text_elem = ET.SubElement(self.input_elem, "text")
        text_elem.text = text

    def add_file(self, file_path: str, name: str):
        content = self.file_processor.read_file(file_path)
        file_elem = ET.SubElement(self.input_elem, "document", name=name)
        file_elem.text = content

    def add_image(self, image_path: str, name: str):
        raise NotImplementedError("Images are not supported in XML format")

    def build_prompt(self) -> str:
        if self.author == "user":
            # Use a custom function to convert the XML to string without escaping
            return self._element_to_string(self.root)
        else:
            return self._extract_simple_text_from_element(self.root)

    def _element_to_string(self, elem: ET.Element, level: int = 0) -> str:
        indent = "  " * level
        result = f"{indent}<{elem.tag}"
        
        for key, value in elem.attrib.items():
            result += f' {key}="{value}"'
        
        if elem.text or len(elem) > 0:
            result += ">"
            if elem.text:
                result += f"\n{indent}  {elem.text.strip()}"
            for child in elem:
                result += "\n" + self._element_to_string(child, level + 1)
            result += f"\n{indent}</{elem.tag}>"
        else:
            result += " />"
        
        return result
    
    def _extract_simple_text_from_element(self, elem: ET.Element) -> str:
        text = elem.text or ""
        for child in elem:
            text += self._extract_simple_text_from_element(child)
            if child.tail:
                text += child.tail
        return text.strip()

    def erase(self):
        self.root = ET.Element("root")
        if self.do_introduction:
            help_content = ET.SubElement(self.root, "text", name="help")
            help_content.text = textwrap.dedent(
                """
                This XML-like object represents the request that you received from the user and will reply to it. 
                It does not follow the full XML specification, but only uses a few tags and the goal is to represent the input in a structured way, while allowing for free-form text without need for escaping.
                
                The input is located inside the <input/> tag, structured as a series of <text/> and <document/> tags. 
                
                The content of your should not be influenced by the fact of using XML for structuring the connections between the pieces of input. Make the best choice for the formatting of the output, with default to use markdown.
                """
            )
        self.input_elem = ET.SubElement(self.root, "input")
