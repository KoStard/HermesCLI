## Renders the subproblems of the current target_node
## Context:
## - subproblems_data: Tuple[PrimitiveSubproblemData]
<%namespace name="xml" file="/macros/xml.mako"/>
${'##'} Subproblems of the current problem
% if not subproblems_data:
No subproblems defined yet.
% else:
<subproblems_list>
%   for subproblem_data in subproblems_data: ## Already sorted by factory method
    ${xml.subproblem_summary_primitive(subproblem_data, indent_level=1)}
%   endfor
</subproblems_list>
% endif
