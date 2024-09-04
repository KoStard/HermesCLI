import pytest
import xml.etree.ElementTree as ET
from hermes.prompt_builders.xml_prompt_builder import XMLPromptBuilder

@pytest.fixture
def xml_prompt_builder():
    return XMLPromptBuilder()

def test_add_text(xml_prompt_builder):
    xml_prompt_builder.add_text("Hello, world!")
    prompt = xml_prompt_builder.build_prompt()
    root = ET.fromstring(prompt)
    assert root.find('text').text == "Hello, world!"

def test_add_text_with_name(xml_prompt_builder):
    xml_prompt_builder.add_text("Hello, world!", name="greeting")
    prompt = xml_prompt_builder.build_prompt()
    root = ET.fromstring(prompt)
    assert root.find('text[@name="greeting"]').text == "Hello, world!"

def test_add_file(xml_prompt_builder):
    xml_prompt_builder.add_file("/path/to/file.txt", "test_file")
    prompt = xml_prompt_builder.build_prompt()
    root = ET.fromstring(prompt)
    assert root.find('document[@name="test_file"]').text == "{file_content:/path/to/file.txt}"

def test_add_image(xml_prompt_builder):
    xml_prompt_builder.add_image("/path/to/image.jpg", "test_image")
    prompt = xml_prompt_builder.build_prompt()
    root = ET.fromstring(prompt)
    image_elem = root.find('image[@name="test_image"]')
    assert image_elem is not None
    assert image_elem.get('path') == "/path/to/image.jpg"

def test_system_message_added_once(xml_prompt_builder):
    xml_prompt_builder.add_text("First text")
    xml_prompt_builder.add_text("Second text")
    prompt = xml_prompt_builder.build_prompt()
    root = ET.fromstring(prompt)
    system_messages = root.findall('systemMessage')
    assert len(system_messages) == 1
    assert system_messages[0].text.startswith("You are a helpful assistant")

def test_build_prompt(xml_prompt_builder):
    xml_prompt_builder.add_text("Hello")
    xml_prompt_builder.add_file("/path/to/file.txt", "test_file")
    xml_prompt_builder.add_image("/path/to/image.jpg", "test_image")
    prompt = xml_prompt_builder.build_prompt()
    root = ET.fromstring(prompt)
    assert root.tag == "input"
    assert len(root.findall('*')) == 4  # systemMessage, text, document, image
