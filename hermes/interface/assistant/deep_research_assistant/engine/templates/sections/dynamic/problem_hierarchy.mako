## Context:
## - file_system_hierarchy_str: str (pre-rendered XML-like string)
## - target_node_title: str
<%namespace name="xml" file="/macros/xml.mako"/>
${'##'} Problem Hierarchy (short)
Notice: The problem hierarchy includes all the problems in the system and their hierarchical relationship, with some metadata.
The current problem is marked with isCurrent="true".

${file_system_hierarchy_str}
