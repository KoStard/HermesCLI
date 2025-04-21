% if not root_node:
Research completed, but no root problem was defined or processed.
% else: # Root node exists
${'#'} Deep Research Completed

${'##'} Problem: ${root_node.title}

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

% for problem_title, artifact_names in sorted(artifacts_by_problem.items()):
${'###'} ${problem_title}

%   for name in sorted(artifact_names):
    <%
        # Construct the relative filepath, ensuring .md extension
        filepath = f"Artifacts/{name}.md"
    %>
- `${filepath}`: ${name}
%   endfor

% endfor

These artifacts contain the valuable outputs of the research process. Each artifact represents a concrete piece of knowledge or analysis that contributes to solving the root problem.
% endif
% endif ## Closes the initial 'if not root_node' block
