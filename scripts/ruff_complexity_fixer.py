#!/usr/bin/env python3
"""
Script to automatically fix ruff C901 complexity warnings using aider.
Runs aider commands in parallel with configurable worker count.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any


class ComplexityFixer:
    def __init__(self, max_workers: int = 3, dry_run: bool = False, aider_script: str = "./aider.sh"):
        self.max_workers = max_workers
        self.dry_run = dry_run
        self.aider_script = aider_script
        self.lock = threading.Lock()
        self.completed = 0
        self.total = 0

    def get_ruff_warnings(self) -> list[dict[str, Any]]:
        """Run ruff and get JSON output of C901 warnings."""
        try:
            # Use full path to executables for security
            uv_path = shutil.which("uv")
            if not uv_path:
                print("Error: 'uv' executable not found in PATH")
                return []

            result = subprocess.run(  # noqa: S603
                [uv_path, "run", "ruff", "check", "--select", "C901", "--output-format", "json"],
                capture_output=True,
                text=True,
                check=False,  # Don't raise exception on non-zero exit
            )
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"Error parsing ruff JSON output: {e}")
            return []

    def format_issue_message(self, warning: dict[str, Any]) -> str:
        """Format the warning into a human-readable message for aider."""
        line = warning["location"]["row"]
        message = warning["message"]

        # Extract function name from message if possible
        # Message format: "`function_name` is too complex (X > Y)"
        if "`" in message:
            function_part = message.split("`")[1]
            complexity_part = message.split("(")[1].split(")")[0] if "(" in message else "unknown complexity"

            issue_description = (
                f"The function '{function_part}' at line {line} is too complex ({complexity_part}). "
                f"Please refactor this function to reduce its cyclomatic complexity by breaking it down into smaller, "
                f"more focused functions. Consider extracting logical blocks into separate methods, "
                f"using early returns to reduce nesting, or applying other refactoring techniques to improve readability "
                f"and maintainability. Make sure the logic remains intact."
            )
        else:
            issue_description = f"Code complexity issue at line {line}: {message}. Please refactor to reduce complexity."

        return issue_description

    def _prepare_relative_path(self, filename: str) -> str:
        """Convert to relative path if possible."""
        try:
            rel_filename = os.path.relpath(filename)
            if len(rel_filename) < len(filename):
                return rel_filename
        except ValueError:
            pass  # Keep absolute path if relative conversion fails
        return filename

    def _build_command(self, filename: str, issue_message: str) -> list[str]:
        """Build the command list for aider."""
        return [self.aider_script, "--file", filename, "--message", f"Fix this issue: {issue_message}", "--yes-always"]

    def _build_result_dict(self, warning: dict[str, Any], filename: str, cmd: list[str]) -> dict[str, Any]:
        """Build the initial result dictionary."""
        return {"warning": warning, "filename": filename, "command": " ".join(cmd), "success": False, "output": "", "error": ""}

    def _handle_dry_run(self, result: dict[str, Any], cmd: list[str], filename: str, issue_message: str) -> dict[str, Any]:
        """Handle dry run mode."""
        with self.lock:
            self.completed += 1
            print(f"[{self.completed}/{self.total}] DRY RUN - Would execute:")
            print(f"  Command: {' '.join(cmd)}")
            print(f"  File: {filename}")
            print(f"  Issue: {issue_message[:100]}...")
            print()
        result["success"] = True
        result["output"] = "DRY RUN - Command not executed"
        return result

    def _execute_command(self, cmd: list[str]) -> tuple[bool, str, str]:
        """Execute the command and return success, stdout, stderr."""
        # Validate aider script path exists before execution
        if not os.path.isfile(cmd[0]):
            return False, "", f"Aider script not found: {cmd[0]}"

        process = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per command
            check=False,
        )
        return process.returncode == 0, process.stdout, process.stderr

    def _update_progress(self, filename: str, success: bool, error_message: str = "") -> None:
        """Update and display progress."""
        with self.lock:
            self.completed += 1
            if success:
                status = "✅ SUCCESS"
                print(f"[{self.completed}/{self.total}] {status} - {filename}")
            else:
                status = "❌ FAILED"
                print(f"[{self.completed}/{self.total}] {status} - {filename}")
                if error_message:
                    print(f"  Error: {error_message[:200]}...")
            print()

    def run_aider_command(self, warning: dict[str, Any]) -> dict[str, Any]:
        """Run aider command for a single warning."""
        filename = warning["filename"]
        issue_message = self.format_issue_message(warning)

        # Make filename relative if possible
        filename = self._prepare_relative_path(filename)

        # Build command and result structure
        cmd = self._build_command(filename, issue_message)
        result = self._build_result_dict(warning, filename, cmd)

        # Handle dry run mode
        if self.dry_run:
            return self._handle_dry_run(result, cmd, filename, issue_message)

        try:
            # Execute command
            success, stdout, stderr = self._execute_command(cmd)

            # Update result
            result["success"] = success
            result["output"] = stdout
            result["error"] = stderr

            # Update progress
            self._update_progress(filename, success, stderr if not success else "")

        except subprocess.TimeoutExpired:
            result["error"] = "Command timed out after 5 minutes"
            self._update_progress(filename, False, "Command timed out after 5 minutes")
        except Exception as e:
            result["error"] = str(e)
            self._update_progress(filename, False, str(e))

        return result

    def process_warnings(self, warnings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process all warnings in parallel."""
        if not warnings:
            print("No C901 warnings found!")
            return []

        self.total = len(warnings)
        print(f"Found {self.total} complexity warnings to process")
        print(f"Using {self.max_workers} parallel workers")
        print(f"Aider script: {self.aider_script}")
        print("=" * 60)

        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_warning = {executor.submit(self.run_aider_command, warning): warning for warning in warnings}

            # Collect results as they complete
            for future in as_completed(future_to_warning):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    warning = future_to_warning[future]
                    print(f"Exception processing {warning['filename']}: {e}")

        return results

    def _print_summary_header(self, total: int, successful: int, failed: int) -> None:
        """Print the summary header section."""
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Total processed: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")

    def _print_failed_files(self, results: list[dict[str, Any]]) -> None:
        """Print details of failed files."""
        print("\nFailed files:")
        for result in results:
            if not result["success"]:
                print(f"  ❌ {result['filename']}")
                if result["error"]:
                    print(f"     Error: {result['error'][:100]}...")

    def print_summary(self, results: list[dict[str, Any]]):
        """Print a summary of the results."""
        if not results:
            return

        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful

        # Print summary header
        self._print_summary_header(len(results), successful, failed)

        # Print failed files if any
        if failed > 0:
            self._print_failed_files(results)

        print()


def main():
    parser = argparse.ArgumentParser(
        description="Fix ruff C901 complexity warnings using aider",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings (3 workers)
  python ruff_complexity_fixer.py

  # Use 5 parallel workers
  python ruff_complexity_fixer.py --workers 5

  # Dry run to see what would be executed
  python ruff_complexity_fixer.py --dry-run

  # Use custom aider script location
  python ruff_complexity_fixer.py --aider-script ./my_aider.sh
        """,
    )

    parser.add_argument("--workers", "-w", type=int, default=3, help="Number of parallel workers (default: 3)")

    parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would be executed without running commands")

    parser.add_argument("--aider-script", default="./aider.sh", help="Path to aider script (default: ./aider.sh)")

    args = parser.parse_args()

    # Validate aider script exists
    if not args.dry_run and not os.path.exists(args.aider_script):
        print(f"Error: Aider script not found: {args.aider_script}")
        sys.exit(1)

    # Create fixer and run
    fixer = ComplexityFixer(max_workers=args.workers, dry_run=args.dry_run, aider_script=args.aider_script)

    print("Getting ruff C901 warnings...")
    warnings = fixer.get_ruff_warnings()

    if not warnings:
        print("No complexity warnings found. Great job! 🎉")
        return

    # Process warnings
    results = fixer.process_warnings(warnings)

    # Print summary
    fixer.print_summary(results)


if __name__ == "__main__":
    main()
