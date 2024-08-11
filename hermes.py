#! /usr/bin/env python

import os
import sys
import argparse
import configparser
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator, Optional
import xml.etree.ElementTree as ET
import readline
import openai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

import anthropic
import boto3
import google.generativeai as genai
from docx import Document
import PyPDF2
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner

def is_binary(file_path):
    """
    Determine if a file is binary or text by checking for non-printable characters.

    :param file_path: Path to the file.
    :return: True if the file is likely binary, False if it is likely text.
    """
    TEXT_CHARACTERS = "".join(map(chr, range(32, 127))) + "\n\r\t\b"
    NULL_BYTE = b'\x00'

    try:
        with open(file_path, 'rb') as f:
            # Read a small portion of the file
            sample = f.read(1024)

        # Check for null bytes, which are common in binary files
        if NULL_BYTE in sample:
            return True

        # Check for non-text characters
        if not all(c in TEXT_CHARACTERS for c in sample.decode('latin1', errors='ignore')):
            return True

        return False
    except (OSError, UnicodeDecodeError):
        # If we encounter an error reading the file, assume it's binary
        return True

class FileProcessor(ABC):
    @abstractmethod
    def read_file(self, file_path: str) -> Any:
        pass
    
    def exists(self, file_path: str) -> bool:
        return os.path.exists(file_path)

    @abstractmethod
    def write_file(self, file_path: str, content: str, mode: str = 'w') -> None:
        pass

class DefaultFileProcessor(FileProcessor):
    def read_file(self, file_path: str) -> str:
        if not self.exists(file_path):
            return "empty"
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif ext == '.docx':
            return self.extract_text_from_docx(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()

    def extract_text_from_pdf(self, file_path: str) -> str:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            return ' '.join(page.extract_text() for page in reader.pages)

    def extract_text_from_docx(self, file_path: str) -> str:
        doc = Document(file_path)
        return ' '.join(paragraph.text for paragraph in doc.paragraphs)

    def write_file(self, file_path: str, content: str, mode: str = 'w') -> None:
        with open(file_path, mode, encoding='utf-8') as file:
            file.write(content)

class BedrockFileProcessor(FileProcessor):
    def read_file(self, file_path: str) -> Dict[str, Any]:
        if not self.exists(file_path):
            return b"empty"

        with open(file_path, 'rb') as file:
            return file.read()

    def write_file(self, file_path: str, content: str, mode: str = 'w') -> None:
        with open(file_path, mode, encoding='utf-8') as file:
            file.write(content)

class PromptFormatter(ABC):
    @abstractmethod
    def format_prompt(self, files: Dict[str, str], prompt: str, special_command: Optional[Dict[str, str]] = None) -> Any:
        pass

class XMLPromptFormatter(PromptFormatter):
    def __init__(self, file_processor: FileProcessor):
        self.file_processor = file_processor

    def format_prompt(self, files: Dict[str, str], prompt: str, special_command: Optional[Dict[str, str]] = None) -> str:
        root = ET.Element("input")
        
        prompt_elem = ET.SubElement(root, "systemMessage")
        prompt_elem.text = "You are a helpful assistant, helping with the requests your manager will assign to you. You gain bonus at the end of each week if you meaningfully help your manager with his goals."
        
        for processed_name, file_path in files.items():
            content = self.file_processor.read_file(file_path)
            file_elem = ET.SubElement(root, "document", name=processed_name)
            file_elem.text = content
        
        prompt_elem = ET.SubElement(root, "prompt")
        prompt_elem.text = prompt

        if special_command:            
            command_elem = ET.SubElement(root, "specialCommand")
            for key, value in special_command.items():
                cmd_elem = ET.SubElement(command_elem, key)
                cmd_elem.text = value

            if 'append' in special_command:
                prompt_elem = ET.SubElement(root, "prompt")
                prompt_elem.text = f"Please provide only the text that should be appended to the file '{special_command['append']}'. Do not include any explanations or additional comments."
            elif 'update' in special_command:
                prompt_elem = ET.SubElement(root, "prompt")
                prompt_elem.text = f"Please provide the entire new content for the file '{special_command['update']}'. The output should contain only the new file content, without any explanations or additional comments."
        
        return ET.tostring(root, encoding='unicode')

class BedrockPromptFormatter(PromptFormatter):
    def __init__(self, file_processor: FileProcessor):
        self.file_processor = file_processor

    def format_prompt(self, files: Dict[str, str], prompt: str, special_command: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        contents = []
    
        for processed_name, file_path in files.items():
            if is_binary(file_path):
                _, ext = os.path.splitext(file_path)
                ext = ext.lower()
                content_bytes = self.file_processor.read_file(file_path)
                if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                    print(f"Adding image {file_path} with format {ext}")
                    contents.append({
                        'image': {
                            'format': ext[1:],
                            'source': {
                                'bytes': content_bytes
                            }
                        }
                    })
                else:
                    print(f"Adding document {processed_name} with format {ext}")
                    contents.append({
                        'document': {
                            'format': ext[1:],
                            'name': processed_name,
                            'source': {
                                'bytes': content_bytes
                            }
                        }
                    })
            else:
                print(f"{file_path} is not binary")
                with open(file_path, 'r') as file:
                    file_content = file.read()
                file_elem = ET.Element("document", name=processed_name)
                file_elem.text = file_content
                contents.append({'text': ET.tostring(file_elem, encoding='unicode')})
        contents.append({'text': prompt})

        if special_command:
            special_prompt = ""
            if 'append' in special_command:
                special_prompt = f"Please provide only the text that should be appended to the file '{special_command['append']}'. Do not include any explanations or additional comments."
            elif 'update' in special_command:
                special_prompt = f"Please provide the entire new content for the file '{special_command['update']}'. The output should contain only the new file content, without any explanations or additional comments."
            if special_prompt:
                contents.append({'text': special_prompt})
        return contents

class ChatModel(ABC):
    def __init__(self, config: configparser.ConfigParser):
        self.config = config

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def send_message(self, message: str) -> Generator[str, None, None]:
        pass

class ClaudeModel(ChatModel):
    def initialize(self):
        api_key = self.config["ANTHROPIC"]["api_key"]
        self.client = anthropic.Anthropic(api_key=api_key)
        self.messages = []

    def send_message(self, message: str) -> Generator[str, None, None]:
        self.messages.append({"role": "user", "content": message})
        with self.client.messages.stream(
            model="claude-3-5-sonnet-20240620",
            messages=self.messages,
            max_tokens=1024
        ) as stream:
            for text in stream.text_stream:
                yield text
        self.messages.append({"role": "assistant", "content": message})

class BedrockModel(ChatModel):
    def __init__(self, config: configparser.ConfigParser, model_tag: str):
        super().__init__(config)
        self.model_tag = model_tag
    
    def initialize(self):
        self.client = boto3.client('bedrock-runtime')
        if self.model_tag == 'claude':
            self.model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
        else:
            self.model_id = 'mistral.mistral-large-2407-v1:0'
        self.messages = []

    def send_message(self, message) -> Generator[str, None, None]:
        if isinstance(message, str):
            message = [{'text': message}]
        # Sorting to put the texts in the end, fails with strange error otherwise
        message.sort(key=lambda x: 'text' in x)
        self.messages.append(self.create_message('user', message))
        response = self.client.converse_stream(
            modelId=self.model_id,
            messages=self.messages
        )

        full_response = ""
        for event in response['stream']:
            if 'contentBlockDelta' in event:
                content = event['contentBlockDelta']['delta'].get('text', '')
                full_response += content
                yield content
            elif 'messageStop' in event:
                break

        self.messages.append(self.create_message('assistant', [{'text': full_response}]))

    def create_message(self, role, content):
        return {
            'role': role,
            'content': content
        }

class GeminiModel(ChatModel):
    def initialize(self):
        api_key = self.config["GEMINI"]["api_key"]
        genai.configure(api_key=api_key)
        self.chat = genai.GenerativeModel('gemini-1.5-pro-exp-0801').start_chat(history=[])

    def send_message(self, message: str) -> Generator[str, None, None]:
        response = self.chat.send_message(message, stream=True, safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        })
        for chunk in response:
            yield chunk.text

class OpenAIModel(ChatModel):
    def initialize(self):
        api_key = self.config["OPENAI"]["api_key"]
        self.client = openai.Client(api_key=api_key)
        self.messages = []

    def send_message(self, message: str) -> Generator[str, None, None]:
        self.messages.append({"role": "user", "content": message})
        stream = self.client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=self.messages,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
        self.messages.append({"role": "assistant", "content": message})

class ChatUI:
    def __init__(self, prints_raw: bool):
        self.console = Console()
        self.prints_raw = prints_raw

    def display_response(self, response_generator: Generator[str, None, None]):
        if self.prints_raw:
            buffer = ""
            for text in response_generator:
                buffer += text
                print(text, end="", flush=True)
            print()
            return buffer
        
        with Live(console=self.console, auto_refresh=False) as live:
            live.update(Spinner("dots", text="Assistant is thinking..."))
            
            buffer = ""
            for text in response_generator:
                buffer += text
                live.update(Markdown("Assistant: \n" + buffer))
                live.refresh()
            
            live.update(Markdown("Assistant: \n" + buffer))
        return buffer

    def get_user_input(self) -> str:
        return input("You: ")

    def display_status(self, message: str):
        self.console.print(message)

class ChatApplication:
    def __init__(self, model: ChatModel, ui: ChatUI, file_processor: FileProcessor):
        self.model = model
        self.ui = ui
        self.file_processor = file_processor

    def run(self, initial_content: str, special_command: Optional[Dict[str, str]] = None):
        if special_command:
            self.model.initialize()
            response = self.ui.display_response(self.model.send_message(initial_content))
            if 'append' in special_command:
                self.append_to_file(special_command['append'], response)
            elif 'update' in special_command:
                self.update_file(special_command['update'], response)
        else:
            latest_input = ""
            while True:
                print("Chat started. Type 'exit', 'quit', or 'q' to end the conversation.")
                self.model.initialize()
                current_initial_content = initial_content
                if latest_input:
                    current_initial_content += '\n\n' + latest_input
                self.ui.display_response(self.model.send_message(current_initial_content))
                
                while True:
                    user_input = self.ui.get_user_input()
                    used_input_lw = user_input.lower()
                    if used_input_lw.startswith('/new') or used_input_lw.startswith('/n'):
                        latest_input = ' '.join(user_input.split()[1:])
                        break
                    if used_input_lw in ['exit', 'quit', 'q']:
                        return

                    self.ui.display_response(self.model.send_message(user_input))

    def append_to_file(self, file_path: str, content: str):
        self.file_processor.write_file(file_path, "\n" + content, mode='a')
        self.ui.display_status(f"Content appended to {file_path}")

    def update_file(self, file_path: str, content: str):
        self.file_processor.write_file(file_path, content, mode='w')
        self.ui.display_status(f"File {file_path} updated")

import re

def process_file_name(file_path: str) -> str:
    """Process the file name to create a consistent reference."""
    base_name = os.path.basename(file_path)
    name, _ = os.path.splitext(base_name)
    result = re.sub(r'[^\w\d\-\(\)\[\]]', '_', name).lower()
    return result

def main():
    parser = argparse.ArgumentParser(description="Multi-model chat application")
    parser.add_argument("model", choices=["claude", "bedrock-claude", "bedrock-mistral", "gemini", "openai"], help="Choose the model to use")
    parser.add_argument("files", nargs='+', help="Input files followed by prompt or prompt file")
    parser.add_argument("--append", "-a", help="Append to the specified file")
    parser.add_argument("--update", "-u", help="Update the specified file")
    parser.add_argument("--raw", "-r", help="Print the output without rendering markdown", action="store_true")
    parser.add_argument("--confirm-before-starting", help="Will confirm before sending the LLM requests, in case you want to prevent unnecessary calls", action="store_true")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config_path = "/Users/kostard/.config/multillmchat/config.ini"
    config.read(config_path)

    files = args.files[:-1]
    prompt_or_file = args.files[-1]

    if os.path.isfile(prompt_or_file):
        print(f"Reading prompt from {prompt_or_file}")
        with open(prompt_or_file, 'r') as f:
            prompt = f.read().strip()
    else:
        prompt = prompt_or_file

    # Process file names
    processed_files = {process_file_name(file): file for file in files}

    special_command = {}
    special_command_raw = {}
    if args.append:
        special_command['append'] = process_file_name(args.append)
        special_command_raw['append'] = args.append
        processed_files[special_command['append']] = args.append
    elif args.update:
        special_command['update'] = process_file_name(args.update)
        special_command_raw['update'] = args.update
        processed_files[special_command['update']] = args.update
    
    if args.confirm_before_starting:
        while True:
            confirm = input("Are you sure you want to continue? (y/n) ")
            if confirm.lower() == 'n':
                return
            elif confirm.lower() == 'y' or not confirm:
                break

    if args.model == "claude":
        model = ClaudeModel(config)
        file_processor = DefaultFileProcessor()
        prompt_formatter = XMLPromptFormatter(file_processor)
    elif args.model == "bedrock-claude":
        model = BedrockModel(config, 'claude')
        file_processor = BedrockFileProcessor()
        prompt_formatter = BedrockPromptFormatter(file_processor)
    elif args.model == "bedrock-mistral":
        model = BedrockModel(config, 'mistral')
        file_processor = BedrockFileProcessor()
        prompt_formatter = BedrockPromptFormatter(file_processor)
    elif args.model == "gemini":
        model = GeminiModel(config)
        file_processor = DefaultFileProcessor()
        prompt_formatter = XMLPromptFormatter(file_processor)
    elif args.model == "openai":
        model = OpenAIModel(config)
        file_processor = DefaultFileProcessor()
        prompt_formatter = XMLPromptFormatter(file_processor)
    else:
        raise ValueError(f"Unsupported model: {args.model}")

    initial_content = prompt_formatter.format_prompt(processed_files, prompt, special_command if special_command else None)

    prints_raw = bool(args.raw)
    ui = ChatUI(prints_raw=prints_raw)
    app = ChatApplication(model, ui, file_processor)
    app.run(initial_content, special_command_raw if special_command_raw else None)

if __name__ == "__main__":
    main()