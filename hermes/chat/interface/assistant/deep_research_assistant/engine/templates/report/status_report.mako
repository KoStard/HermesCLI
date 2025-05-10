<%namespace name="status_helpers" file="status_helpers.mako"/>

================================================================================
=== Deep Research Assistant - Comprehensive Progress Report ===
Current Problem: ${current_node.get_name()}
Criteria Status: ${current_node.get_criteria_met_count()}/${current_node.get_criteria_total_count()} met

=== Full Problem Tree ===
${status_helpers.render_node_status(root_node, "", True, current_node)}
================================================================================
