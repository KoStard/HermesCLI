import argparse
from ..workflows.executor import WorkflowExecutor
from ..chat_models.base import ChatModel

def add_workflow_arguments(parser: argparse.ArgumentParser):
    parser.add_argument("--workflow", help="Specify a workflow YAML file to execute")

def execute_workflow(args: argparse.Namespace, model: ChatModel):
    if not args.workflow:
        print("No workflow file specified. Use --workflow to specify a workflow YAML file.")
        return

    executor = WorkflowExecutor(args.workflow, model)
    result = executor.execute()
    
    print("Workflow execution completed.")
    print("Final context:")
    for key, value in result.items():
        print(f"{key}: {value}")
