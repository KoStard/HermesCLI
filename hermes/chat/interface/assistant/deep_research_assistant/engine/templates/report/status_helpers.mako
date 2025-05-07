<%def name="render_node_status(node, prefix, is_last, current_node)">\
    <%
        # --- Prepare data needed for this node ---
        branch = u"└── " if is_last else u"├── "
        is_current = node == current_node
        node_marker = u"→ " if is_current else ""
        criteria_met = node.get_criteria_met_count()
        criteria_total = node.get_criteria_total_count()
        artifacts_count = len(node.artifacts)
        subproblems_count = len(node.subproblems)
        status_emoji = node.get_status_emoji()
        new_prefix = prefix + (u"    " if is_last else u"│   ")
        subproblems = list(node.subproblems.values())
    %>\
${prefix}${branch}${node_marker}${status_emoji} ${node.title} [${criteria_met}/${criteria_total}]\
% if artifacts_count > 0:
 🗂️${artifacts_count}\
% endif
% if subproblems_count > 0:
 🔍${subproblems_count}\
% endif

% for i, subproblem in enumerate(subproblems):
    <% is_last_child = i == len(subproblems) - 1 %>\
${render_node_status(subproblem, new_prefix, is_last_child, current_node)}\
% endfor
</%def>\
