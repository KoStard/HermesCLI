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

## --- Hierarchy Formatting Macros (Using Primitive Data) ---

<%def name="node_attributes_primitive(node_data)">
    <%
        # Helper to generate common node attributes string from primitive data
        # Works with PrimitiveNodePathData or PrimitiveSubproblemData
        attrs = {
            "title": node_data.title,
            "depth": getattr(node_data, 'depth', '?'), # Depth only in PathData
            "status": getattr(node_data, 'status_label', '?'), # Status only in SubproblemData (or needs adding to PathData)
            "criteriaProgress": getattr(node_data, 'criteria_status', f"[{sum(getattr(node_data, 'criteria_done', []))}/{len(getattr(node_data, 'criteria', []))} criteria met]"),
            "artifacts": getattr(node_data, 'artifacts_count', '?'),
        }
    %>
${' '.join(f'{k}="{v}"' for k, v in attrs.items())}
</%def>

<%def name="node_content_primitive(node_data, indent_level=1)">
    <%
        # Renders definition and criteria from primitive data
        # Works with PrimitiveNodePathData or PrimitiveSubproblemData
        indent = "  " * indent_level
    %>
    ${indent}<problem_definition>${node_data.problem_definition}</problem_definition>
    % if node_data.criteria:
    ${indent}<criteria>
    %   for i, (criterion, done) in enumerate(zip(node_data.criteria, node_data.criteria_done)):
        ${indent}  <criterion status="${'✓' if done else '□'}">${criterion}</criterion>
    %   endfor
    ${indent}</criteria>
    % endif
</%def>

<%def name="subproblem_summary_primitive(subproblem_data, indent_level=0)">
    <%
        # Renders a full summary from PrimitiveSubproblemData
        indent = "  " * indent_level
    %>
${indent}<subproblem ${node_attributes_primitive(subproblem_data)}>
${node_content_primitive(subproblem_data, indent_level + 1)}
${indent}</subproblem>
</%def>

<%def name="subproblem_reference_primitive(subproblem_data, indent_level=0)">
    <%
        # Renders a reference (attributes only) from PrimitiveSubproblemData
        indent = "  " * indent_level
    %>
${indent}<subproblem ${node_attributes_primitive(subproblem_data)} inPath="false" />
</%def>

<%def name="render_path_node_primitive(path_nodes_data, current_index, target_depth, indent_level=0)">
    <%
        # Recursive macro for problem_path_hierarchy using Tuple[PrimitiveNodePathData]
        indent = "  " * indent_level
        node_data = path_nodes_data[current_index]
        is_target_node = (current_index == target_depth)
    %>
${indent}<node ${node_attributes_primitive(node_data)} isCurrent="${str(is_target_node).lower()}">
${node_content_primitive(node_data, indent_level + 1)}
    % if not is_target_node:
        <% next_node_in_path_data = path_nodes_data[current_index + 1] %>
        ${indent}  <subproblems>
        % for sibling_data in node_data.sibling_subproblems:
            ## Render siblings that are not the next node in the path as references
            ${subproblem_reference_primitive(sibling_data, indent_level + 2)}
        % endfor
        ## Render the next node in the path recursively
        ${render_path_node_primitive(path_nodes_data, current_index + 1, target_depth, indent_level + 2)}
        ${indent}  </subproblems>
    % endif
${indent}</node>
</%def>


## --- Knowledge Base Macro (Using Primitive Data) ---

<%def name="knowledge_entry_primitive(entry_data, author_title_max_len=50)">
    <%
        # Renders a knowledge entry from PrimitiveKnowledgeEntryData
        # Truncate author title for display if needed
        display_author = (entry_data.author_node_title[:author_title_max_len] + '...'
                          if len(entry_data.author_node_title) > author_title_max_len
                          else entry_data.author_node_title)
    %>
    <knowledge_entry timestamp="${entry_data.timestamp}" author_node="${display_author}">
        % if entry_data.title:
        <title>${entry_data.title}</title>
        % endif
        % if entry_data.tags:
        <tags>${', '.join(entry_data.tags)}</tags>
        % endif
        <content>
${entry_data.content}
        </content>
    </knowledge_entry>
</%def>
