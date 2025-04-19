<%namespace name="xml" file="/macros/xml.mako"/>
${'##'} Problem Hierarchy (short)
Notice: The problem hierarchy includes all the problems in the system and their hierarchical relationship, with some metadata.
The current problem is marked with isCurrent="true".

${file_system.get_problem_hierarchy(target_node)}
