## Renders the hierarchy path from root to the current target_node
## Context:
## - path_nodes_data: Tuple[PrimitiveNodePathData]
<%namespace name="xml" file="/macros/xml.mako"/>
${'##'} Problem Path Hierarchy (from root to current)
% if not path_nodes_data:
No problem hierarchy available (root node likely not set).
% elif len(path_nodes_data) == 1:
Currently at the root problem.
% else:
<problem_path_hierarchy>
    <%
        # Start rendering from the root node (index 0)
        # path_nodes_data is already ordered correctly
        target_depth_index = len(path_nodes_data) - 1
    %>
    ${xml.render_path_node_primitive(path_nodes_data, 0, target_depth_index, indent_level=1)}
</problem_path_hierarchy>
% endif
