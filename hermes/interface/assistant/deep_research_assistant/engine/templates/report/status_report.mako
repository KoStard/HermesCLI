<%namespace name="status_helpers" file="status_helpers.mako"/>

% if not problem_defined:

=== Deep Research Assistant ===
Status: No problem defined yet
% elif not current_node:

=== Deep Research Assistant ===
Status: No current node
% else:

================================================================================
=== Deep Research Assistant - Comprehensive Progress Report ===
Current Problem: ${current_node.title}
Criteria Status: ${current_node.get_criteria_met_count()}/${current_node.get_criteria_total_count()} met

=== Full Problem Tree ===
% if root_node:
${status_helpers.render_node_status(root_node, "", True, current_node)}
% else:
No root node defined.
% endif
================================================================================

% endif
