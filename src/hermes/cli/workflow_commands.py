import argparse
from typing import List
from ..workflows.executor import WorkflowExecutor
from ..chat_models.base import ChatModel

def add_workflow_arguments(parser: argparse.ArgumentParser):
    parser.add_argument("--workflow", help="Specify a workflow YAML file to execute")
    parser.add_argument("--input-files", nargs="*", help="Input files for the workflow")
    parser.add_argument("--initial-prompt", help="Initial prompt for the workflow")

def execute_workflow(args: argparse.Namespace, model: ChatModel):
    if not args.workflow:
        print("No workflow file specified. Use --workflow to specify a workflow YAML file.")
        return

    input_files: List[str] = args.input_files or []
    initial_prompt: str = args.initial_prompt or ""

    executor = WorkflowExecutor(args.workflow, model, input_files, initial_prompt)
    result = executor.execute()
    
    print("Workflow execution completed.")
    print("Final context:")
    for key, value in result.items():
        print(f"{key}: {value}")
