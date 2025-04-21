## Template for rendering the AutoReply content
<%namespace name="xml" file="/macros/xml.mako"/>
## Context variables expected:
## - confirmation_request: Optional[str]
## - error_report: str
## - command_outputs: List[Tuple[str, dict]]  (dict has 'args', 'output')
## - messages: List[Tuple[str, str]] (message, origin_node_title)
## - rendered_dynamic_sections: List[Tuple[int, str]] (section_index, rendered_content_or_error)
## - per_command_output_maximum_length: Optional[int]
## - ContentTruncator: class (for calling static truncate method)
${'#'} Automatic Reply

If there are commands you sent in your message and they have any errors or outputs, you'll see them below.
If you don't see a command report, then no commands were executed!
% if confirmation_request:
${'###'} Confirmation Required
${confirmation_request}
% endif

% if error_report:
${error_report}
% endif

${'###'} Command Outputs
% if command_outputs:
%   for cmd_name, output_data in command_outputs:

${'####'} <<< ${cmd_name}
%     if output_data.get("args", {}):
Arguments: ${", ".join(f"{k}: {v}" for k, v in output_data.get("args", {}).items())}

%     endif
```
${ContentTruncator.truncate(
    output_data.get("output", ""),
    per_command_output_maximum_length,
    additional_help="To see the full content again, rerun the command."
)}
```
%   endfor
% else:

No command outputs
% endif
% if messages:

${'###'} Internal Automatic Messages
%   for message, origin_node_title in messages:

${'####'} From: ${origin_node_title}
```
${message}
```
%   endfor
% endif

% if rendered_dynamic_sections:
${'###'} Updated Interface Sections

The following interface sections have been updated:
%   for section_index, rendered_content in rendered_dynamic_sections:
## --- Section Index ${section_index} ---
${rendered_content}
%   endfor
% endif
