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

from utils.file_utils import is_binary, process_file_name

from file_processors.default import DefaultFileProcessor
from file_processors.bedrock import BedrockFileProcessor

from prompt_formatters.xml import XMLPromptFormatter
from prompt_formatters.bedrock import BedrockPromptFormatter

from chat_models.claude import ClaudeModel
from chat_models.bedrock import BedrockModel
from chat_models.gemini import GeminiModel
from chat_models.openai import OpenAIModel

from ui.chat_ui import ChatUI

from chat_application import ChatApplication

def main():
    parser = argparse.ArgumentParser(description="Multi-model chat application")
    parser.add_argument("model", choices=["claude", "bedrock-claude", "bedrock-claude-3.5", "bedrock-opus", "bedrock-mistral", "gemini", "openai"], help="Choose the model to use")
    parser.add_argument("files", nargs='+', help="Input files followed by prompt or prompt file")
    parser.add_argument("--append", "-a", help="Append to the specified file")
    parser.add_argument("--update", "-u", help="Update the specified file")
    parser.add_argument("--raw", "-r", help="Print the output without rendering markdown", action="store_true")
    parser.add_argument("--confirm-before-starting", help="Will confirm before sending the LLM requests, in case you want to prevent unnecessary calls", action="store_true")
    parser.add_argument("--ask-for-user-prompt", "-up", action="store_true", help="Prompt for additional user input before sending the initial request")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config_path = "~/.config/multillmchat/config.ini"
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
    elif args.model == "bedrock-claude-3.5":
        model = BedrockModel(config, 'claude-3.5')
        file_processor = BedrockFileProcessor()
        prompt_formatter = BedrockPromptFormatter(file_processor)
    elif args.model == "bedrock-opus":
        model = BedrockModel(config, 'opus')
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
    app = ChatApplication(model, ui, file_processor, prompt_formatter)
    app.run(initial_content, special_command_raw if special_command_raw else None, args.ask_for_user_prompt)

if __name__ == "__main__":
    main()
