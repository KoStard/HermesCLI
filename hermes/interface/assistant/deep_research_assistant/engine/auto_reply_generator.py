from typing import Dict, List, Optional


class AutoReplyGenerator:
    """
    Responsible for generating automatic replies based on command execution results.
    This class handles formatting and generation of all automatic responses.
    """

    def generate_auto_reply(
        self, 
        error_report: str, 
        command_outputs: Dict[str, List[Dict[str, any]]]
    ) -> str:
        """
        Generate an automatic reply based on command execution results
        
        Args:
            error_report: Error report from command parsing/execution
            command_outputs: Dictionary of command outputs
            
        Returns:
            Formatted automatic reply string
        """
        auto_reply = f'Automatic Reply: The status of the research is "In Progress". Please continue the research or mark it as done using `focus_up` command.'
        
        # Add error report if any
        if error_report:
            auto_reply += f"\n\n{error_report}"

        # Add command outputs if any
        if command_outputs:
            auto_reply += "\n\n### Command Outputs\n"
            for cmd_name, outputs in command_outputs.items():
                for output_data in outputs:
                    auto_reply += f"\n#### {cmd_name}\n"
                    # Format arguments
                    args_str = ", ".join(
                        f"{k}: {v}" for k, v in output_data["args"].items()
                    )
                    if args_str:
                        auto_reply += f"Arguments: {args_str}\n\n"
                    # Add the output
                    auto_reply += f"```\n{output_data['output']}\n```\n"

        return auto_reply
