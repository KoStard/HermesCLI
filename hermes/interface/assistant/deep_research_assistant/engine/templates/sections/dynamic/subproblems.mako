## Renders the subproblems of the current target_node
<%namespace name="xml" file="/macros/xml.mako"/>
${'##'} Subproblems of the current problem
% if not target_node.subproblems:
No subproblems defined yet.
% else:
<subproblems_list>
%   for title, subproblem in sorted(target_node.subproblems.items()):
    ${xml.subproblem_summary(subproblem, indent_level=1)}
%   endfor
</subproblems_list>
% endif
