#!/usr/bin/env python3
"""
Script to automatically fix all ruff warnings using aider.
Groups warnings by file and processes multiple warnings per file.
Runs aider commands in parallel with configurable worker count.
"""

import argparse
import json
import os
import subprocess
import sys
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any


@dataclass
class RuffOptions:
    """Configuration options for ruff."""

    select: str | None = None
    ignore: str | None = None


class RuffFixer:
    def __init__(
        self,
        max_workers: int = 3,
        dry_run: bool = False,
        aider_script: str = "./aider.sh",
        ruff_options: RuffOptions = None,
    ):
        self.max_workers = max_workers
        self.dry_run = dry_run
        self.aider_script = aider_script
        self.ruff_options = ruff_options or RuffOptions()
        self.lock = threading.Lock()
        self.completed = 0
        self.total = 0

    def get_ruff_warnings(self) -> list[dict[str, Any]]:
        """Run ruff and get JSON output of warnings."""
        cmd = ["uv", "run", "ruff", "check", "--output-format", "json"]

        # Add select/ignore if specified
        if self.ruff_options.select:
            cmd.extend(["--select", self.ruff_options.select])
        if self.ruff_options.ignore:
            cmd.extend(["--ignore", self.ruff_options.ignore])
        try:
            result = subprocess.run(  # noqa: S603
                cmd, capture_output=True, text=True
            )
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"Error parsing ruff JSON output: {e}")
            return []

    def group_warnings_by_file(self, warnings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Group warnings by filename."""
        grouped = defaultdict(list)
        for warning in warnings:
            filename = warning["filename"]
            # Make filename relative to current directory if possible
            try:
                rel_filename = os.path.relpath(filename)
                if len(rel_filename) < len(filename):
                    filename = rel_filename
                warning["filename"] = filename  # Update the warning with relative path
            except ValueError:
                pass  # Keep absolute path if relative conversion fails

            grouped[filename].append(warning)

        return grouped

    def format_issue_messages(self, warnings: list[dict[str, Any]]) -> str:
        """Format multiple warnings into a human-readable message for aider."""
        messages = []

        for i, warning in enumerate(warnings, 1):
            rule_id = warning.get("code", "")
            line = warning["location"]["row"]
            message = warning["message"]

            # Format the issue message
            issue = f"{i}. Line {line}: {rule_id} - {message}"
            messages.append(issue)
        # Combine all issues into one message
        return (
            f"Please fix these {len(warnings)} issues in this file:\n\n"
            + "\n".join(messages)
            + "\n\nApply best practices when fixing each issue. Make sure the logic remains intact."
        )

    def run_aider_command(self, filename: str, warnings: list[dict[str, Any]]) -> dict[str, Any]:
        """Run aider command for warnings in a single file."""
        issue_message = self.format_issue_messages(warnings)

        cmd = [self.aider_script, "--file", filename, "--message", f"Fix these issues: {issue_message}", "--yes-always"]

        result = {
            "filename": filename,
            "warnings": warnings,
            "warning_count": len(warnings),
            "command": " ".join(cmd),
            "success": False,
            "output": "",
            "error": "",
        }

        if self.dry_run:
            with self.lock:
                self.completed += 1
                print(f"[{self.completed}/{self.total}] DRY RUN - Would execute:")
                print(f"  Command: {' '.join(cmd)}")
                print(f"  File: {filename}")
                print(f"  Issues: {len(warnings)} warnings")
                print()
            result["success"] = True
            result["output"] = "DRY RUN - Command not executed"
            return result

        try:
            # Run the aider command with security checks
            process = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout per command (increased for multiple issues)
                check=False,  # We'll handle return codes ourselves
                shell=False,  # Never use shell=True for security
            )

            result["success"] = process.returncode == 0
            result["output"] = process.stdout
            result["error"] = process.stderr

            with self.lock:
                self.completed += 1
                status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
                print(f"[{self.completed}/{self.total}] {status} - {filename} ({len(warnings)} warnings)")
                if not result["success"]:
                    print(f"  Error: {process.stderr[:200]}...")
                print()

        except subprocess.TimeoutExpired:
            result["error"] = "Command timed out after 10 minutes"
            with self.lock:
                self.completed += 1
                print(f"[{self.completed}/{self.total}] ⏰ TIMEOUT - {filename}")
                print()
        except Exception as e:
            result["error"] = str(e)
            with self.lock:
                self.completed += 1
                print(f"[{self.completed}/{self.total}] 💥 ERROR - {filename}: {e}")
                print()

        return result

    def process_files(self, grouped_warnings: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        """Process all files with warnings in parallel."""
        if not grouped_warnings:
            print("No warnings found!")
            return []

        self.total = len(grouped_warnings)
        total_warnings = sum(len(warnings) for warnings in grouped_warnings.values())
        print(f"Found {total_warnings} warnings across {self.total} files")
        print(f"Using {self.max_workers} parallel workers")
        print(f"Aider script: {self.aider_script}")
        print("=" * 60)

        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.run_aider_command, filename, warnings): filename for filename, warnings in grouped_warnings.items()
            }

            # Collect results as they complete
            for future in as_completed(future_to_file):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    filename = future_to_file[future]
                    print(f"Exception processing {filename}: {e}")

        return results

    def _print_summary_header(self, results: list[dict[str, Any]]):
        """Print the header section of the summary."""
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        total_warnings = sum(r["warning_count"] for r in results)
        fixed_warnings = sum(r["warning_count"] for r in results if r["success"])

        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Total files processed: {len(results)}")
        print(f"Total warnings: {total_warnings}")
        print(f"Files successfully processed: {successful}")
        print(f"Warnings potentially fixed: {fixed_warnings}")
        print(f"Files failed: {failed}")

    def _print_failed_files(self, results: list[dict[str, Any]]):
        """Print details about files that failed processing."""
        failed = sum(1 for r in results if not r["success"])

        if failed > 0:
            print("\nFailed files:")
            for result in results:
                if not result["success"]:
                    print(f"  ❌ {result['filename']} ({result['warning_count']} warnings)")
                    if result["error"]:
                        print(f"     Error: {result['error'][:100]}...")

        print()

    def print_summary(self, results: list[dict[str, Any]]):
        """Print a summary of the results."""
        if not results:
            return

        self._print_summary_header(results)
        self._print_failed_files(results)


def main():
    parser = argparse.ArgumentParser(
        description="Fix all ruff warnings using aider, grouped by file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings (3 workers, all warnings)
  python ruff_fixer.py

  # Use 5 parallel workers
  python ruff_fixer.py --workers 5

  # Only fix specific rule categories
  python ruff_fixer.py --select E,F,W

  # Ignore certain rule categories
  python ruff_fixer.py --ignore E501,E203

  # Dry run to see what would be executed
  python ruff_fixer.py --dry-run

  # Use custom aider script location
  python ruff_fixer.py --aider-script ./my_aider.sh
        """,
    )

    parser.add_argument("--workers", "-w", type=int, default=3, help="Number of parallel workers (default: 3)")

    parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would be executed without running commands")

    parser.add_argument("--aider-script", default="./aider.sh", help="Path to aider script (default: ./aider.sh)")

    parser.add_argument("--select", help="Comma-separated list of rule codes to include (e.g., E,F,W)")

    parser.add_argument("--ignore", help="Comma-separated list of rule codes to ignore (e.g., E501,E203)")

    args = parser.parse_args()

    # Validate aider script exists
    if not args.dry_run and not os.path.exists(args.aider_script):
        print(f"Error: Aider script not found: {args.aider_script}")
        sys.exit(1)

    # Create ruff options
    ruff_options = RuffOptions(select=args.select, ignore=args.ignore)

    # Create fixer and run
    fixer = RuffFixer(max_workers=args.workers, dry_run=args.dry_run, aider_script=args.aider_script, ruff_options=ruff_options)

    print("Getting ruff warnings...")
    warnings = fixer.get_ruff_warnings()

    if not warnings:
        print("No warnings found. Great job! 🎉")
        return

    # Group warnings by file
    grouped_warnings = fixer.group_warnings_by_file(warnings)

    # Process files with warnings
    results = fixer.process_files(grouped_warnings)

    # Print summary
    fixer.print_summary(results)


if __name__ == "__main__":
    main()
