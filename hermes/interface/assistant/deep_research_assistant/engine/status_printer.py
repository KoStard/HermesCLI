from typing import Optional

from .file_system import FileSystem, Node
from .task_manager import TaskManager
from .task_queue import TaskStatus


class StatusPrinter:
    """
    Responsible for printing the current status of the research to the console.
    This class handles all console output formatting related to status reporting.
    """

    def print_status(
        self, 
        problem_defined: bool, 
        current_node: Optional[Node], 
        task_manager: TaskManager,
        file_system: FileSystem
    ) -> None:
        """Print the current status of the research to STDOUT"""
        if not problem_defined:
            print("\n=== Deep Research Assistant ===")
            print("Status: No problem defined yet")
            return

        if not current_node:
            print("\n=== Deep Research Assistant ===")
            print("Status: No current node")
            return

        print("\n" + "=" * 80)
        print("=== Deep Research Assistant - Comprehensive Progress Report ===")

        # Print current problem info
        print(f"Current Problem: {current_node.title}")

        # Print criteria status
        criteria_met = current_node.get_criteria_met_count()
        criteria_total = current_node.get_criteria_total_count()
        print(f"Criteria Status: {criteria_met}/{criteria_total} met")

        # Print task status information
        if task_manager.current_task_id:
            current_task = task_manager.task_queue.get_task(
                task_manager.current_task_id
            )
            if current_task:
                print(f"Task Status: {current_task.status.value}")

                # Print pending child tasks if any
                if (
                    task_manager.current_task_id
                    in task_manager.task_relationships
                ):
                    child_task_ids = task_manager.task_relationships[
                        task_manager.current_task_id
                    ]
                    pending_children = 0
                    running_children = 0
                    completed_children = 0
                    failed_children = 0

                    for child_id in child_task_ids:
                        child_task = task_manager.task_queue.get_task(child_id)
                        if child_task:
                            if child_task.status == TaskStatus.PENDING:
                                pending_children += 1
                            elif child_task.status == TaskStatus.RUNNING:
                                running_children += 1
                            elif child_task.status == TaskStatus.COMPLETED:
                                completed_children += 1
                            elif child_task.status == TaskStatus.FAILED:
                                failed_children += 1

                    if (
                        pending_children
                        + running_children
                        + completed_children
                        + failed_children
                        > 0
                    ):
                        print(
                            f"Child Tasks: {pending_children} pending, {running_children} running, "
                            f"{completed_children} completed, {failed_children} failed"
                        )

        # Print full problem tree with detailed metadata
        print("\n=== Full Problem Tree ===")
        self._print_problem_tree(file_system.root_node, "", True, current_node)

        print("=" * 80 + "\n")

    def _print_problem_tree(self, node: Node, prefix: str, is_last: bool, current_node: Node):
        """Print a tree representation of the problem hierarchy with metadata"""
        if not node:
            return

        # Determine the branch symbol
        branch = "└── " if is_last else "├── "

        # Highlight current node
        is_current = node == current_node
        node_marker = "→ " if is_current else ""

        # Gather metadata
        criteria_met = node.get_criteria_met_count()
        criteria_total = node.get_criteria_total_count()
        artifacts_count = len(node.artifacts)
        subproblems_count = len(node.subproblems)

        # Get status emoji
        status_emoji = node.get_status_emoji()

        # Format the node line with metadata
        node_info = f"{node_marker}{status_emoji} {node.title} [{criteria_met}/{criteria_total}]"
        if artifacts_count > 0:
            node_info += f" 🗂️{artifacts_count}"
        if subproblems_count > 0:
            node_info += f" 🔍{subproblems_count}"

        # Print the current node
        print(f"{prefix}{branch}{node_info}")

        # Prepare prefix for children
        new_prefix = prefix + ("    " if is_last else "│   ")

        # Print all subproblems
        subproblems = list(node.subproblems.values())
        for i, subproblem in enumerate(subproblems):
            is_last_child = i == len(subproblems) - 1
            self._print_problem_tree(
                subproblem, new_prefix, is_last_child, current_node
            )
