## Renders the hierarchy path from root to the current target_node
<%namespace name="xml" file="/macros/xml.mako"/>
${'##'} Problem Path Hierarchy (from root to current)
% if not parent_chain or len(parent_chain) == 0:
No problem hierarchy available (root node likely not set).
% elif len(parent_chain) == 1:
Currently at the root problem.
% else:
<problem_path_hierarchy>
    <%
        # Start rendering from the root node (index 0)
        # parent_chain is passed from the context by DeepResearcherInterface
        root_node = parent_chain[0]
        target_depth_index = len(parent_chain) - 1
    %>
    ${xml.render_path_node(root_node, parent_chain, 0, target_depth_index, indent_level=1)}
</problem_path_hierarchy>
% endif
