<%def name="section(name, content='')">
<${name}>
${content}
</${name}>
</%def>
<%def name="artifact(name, content, **attrs)">
<artifact name="${name}"${' '.join(f' {k}="{v}"' for k, v in attrs.items())}>
${content}
</artifact>
</%def>

<%def name="separator()">
<separator>---------------------</separator>
</%def>

## --- Hierarchy Formatting Macros ---
<%def name="node_attributes(node)">
    <%
        # Helper to generate common node attributes string
        attrs = {
            "title": node.title,
            "status": node.status.value,
            "criteriaProgress": f"{node.get_criteria_met_count()}/{node.get_criteria_total_count()}",
            "depth": node.depth_from_root,
            "artifacts": len(node.artifacts),
        }
    %>
${' '.join(f'{k}="{v}"' for k, v in attrs.items())}
</%def>

<%def name="node_content(node, indent_level=1)">
    <% indent = "  " * indent_level %>
    ${indent}<problem_definition>${node.problem_definition | h}</problem_definition>
    % if node.criteria:
    ${indent}<criteria>
    %   for i, (criterion, done) in enumerate(zip(node.criteria, node.criteria_done)):
        ${indent}  <criterion status="${'✓' if done else '□'}">${criterion | h}</criterion>
    %   endfor
    ${indent}</criteria>
    % endif
</%def>

<%def name="subproblem_summary(subproblem, indent_level=0)">
    <% indent = "  " * indent_level %>
${indent}<subproblem ${node_attributes(subproblem)}>
${node_content(subproblem, indent_level + 1)}
${indent}</subproblem>
</%def>

<%def name="subproblem_reference(subproblem, indent_level=0)">
    <% indent = "  " * indent_level %>
${indent}<subproblem title="${subproblem.title | h}" status="${subproblem.status.value}" inPath="false" />
</%def>

<%def name="render_path_node(node, chain, current_index, target_depth, indent_level=0)">
    <%
        # Recursive macro for problem_path_hierarchy
        indent = "  " * indent_level
        is_target_node = (current_index == target_depth)
    %>
${indent}<node ${node_attributes(node)} isCurrent="${str(is_target_node).lower()}">
${node_content(node, indent_level + 1)}
    % if not is_target_node:
        <% next_node_in_chain = chain[current_index + 1] %>
        ${indent}  <subproblems>
        % for title, subproblem in sorted(node.subproblems.items()):
            % if subproblem == next_node_in_chain:
                ${render_path_node(subproblem, chain, current_index + 1, target_depth, indent_level + 2)}
            % else:
                ${subproblem_reference(subproblem, indent_level + 2)}
            % endif
        % endfor
        ${indent}  </subproblems>
    % endif
${indent}</node>
</%def>
