<%namespace name="xml" file="/macros/xml.mako"/>
<%
# Define the separator used by Python code to split sections
# IMPORTANT: This exact string is used in interface.py to split the rendered output.
separator = "<!-- DYNAMIC_SECTION_SEPARATOR -->"
%>
<%include file="sections/dynamic/header.mako"/>
${separator}
<%include file="sections/dynamic/permanent_logs.mako"/>
${separator}
<%include file="sections/dynamic/budget.mako"/>
${separator}
<%include file="sections/dynamic/artifacts.mako" args="external_files=external_files,node_artifacts=node_artifacts,truncator=ContentTruncator"/>
${separator}
<%include file="sections/dynamic/problem_hierarchy.mako"/>
${separator}
<%include file="sections/dynamic/criteria.mako" args="criteria=target_node.criteria,criteria_done=target_node.criteria_done"/>
${separator}
<%include file="sections/dynamic/subproblems.mako"/>
${separator}
<%include file="sections/dynamic/problem_path_hierarchy.mako"/>
${separator}
<%include file="sections/dynamic/goal.mako"/>
