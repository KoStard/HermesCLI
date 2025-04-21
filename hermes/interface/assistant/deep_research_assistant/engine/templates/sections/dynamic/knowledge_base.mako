## Renders the shared knowledge base
## Context:
## - knowledge_entries_data: Tuple[PrimitiveKnowledgeEntryData]
<%namespace name="xml" file="/macros/xml.mako"/>
${'#'} Shared Knowledge Base

% if not knowledge_entries_data:
<knowledge_base>
No knowledge entries added yet. Use the 'add_knowledge' command to contribute.
</knowledge_base>
% else:
<knowledge_base>
    <knowledge_intro>
    Entries added by all assistants working on this research project. Sorted newest first.
    </knowledge_intro>
    % for entry_data in knowledge_entries_data:
        ${xml.knowledge_entry_primitive(entry_data)}
    % endfor
</knowledge_base>
% endif
