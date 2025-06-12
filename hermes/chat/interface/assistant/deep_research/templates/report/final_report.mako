% if not root_node:
Research completed, but no root problem was defined or processed.
% else: # Root node exists
${'#'} Deep Research Completed

${'##'} Problem: ${root_node.get_title()}

% if budget_info:
${'##'} Budget Usage

% if budget_info.get('budget') is None:
No budget limits were set for this research.
% else:
- Initial budget: ${budget_info.get('budget')} message cycles
- Used: ${budget_info.get('used')} message cycles
- Remaining: ${budget_info.get('remaining')} message cycles
% if budget_info.get('since_last_start'):
- Used since last start: ${budget_info.get('since_last_start')} message cycles
% endif
% endif

% endif

% if root_completion_message:
${'##'} Final Message from Root Task

${root_completion_message}

% endif

% if not artifacts_by_problem:
${'##'} Summary of Generated Artifacts

Research completed, but no artifacts were generated.
% else:
${'##'} Summary of Generated Artifacts

The research has been completed and the following artifacts have been created:

% for problem_title, artifacts in sorted(artifacts_by_problem.items()):
${'###'} ${problem_title}

%   for artifact in sorted(artifacts, key=lambda x: x['name']):
- `${artifact['relative_path']}`: ${artifact['name']}
%   endfor

% endfor

These artifacts contain the valuable outputs of the research process. Each artifact represents a concrete piece of knowledge or analysis that contributes to solving the root problem.
% endif
% endif ## Closes the initial 'if not root_node' block
