<%def name="render_node_status(node, prefix, is_last)">\
    <%
        # --- Prepare data needed for this node ---
        branch = u"└── " if is_last else u"├── "
        criteria_met = node.get_criteria_met_count()
        criteria_total = node.get_criteria_total_count()
        artifacts_count = len(node.get_artifacts())
        subproblems_count = len(node.list_child_nodes())
        status_emoji = get_status_emoji(node.get_problem_status())
        new_prefix = prefix + (u"    " if is_last else u"│   ")
        subproblems = list(node.list_child_nodes())
    %>\
${prefix}${branch}${status_emoji} ${node.get_title()} [${criteria_met}/${criteria_total}]\
% if artifacts_count > 0:
 🗂️${artifacts_count}\
% endif
% if subproblems_count > 0:
 🔍${subproblems_count}\
% endif

% for i, subproblem in enumerate(subproblems):
    <% is_last_child = i == len(subproblems) - 1 %>\
${render_node_status(subproblem, new_prefix, is_last_child)}\
% endfor
</%def>\
