## Renders the shared knowledge base
<%namespace name="xml" file="/macros/xml.mako"/>
${'#'} Shared Knowledge Base

% if not knowledge_base:
<knowledge_base>
No knowledge entries added yet. Use the 'add_knowledge' command to contribute.
</knowledge_base>
% else:
<knowledge_base>
    <knowledge_intro>
    Entries added by all assistants working on this research project. Sorted newest first.
    </knowledge_intro>
    ${xml.separator()}
    % for entry in sorted(knowledge_base, key=lambda x: x.timestamp, reverse=True):
        ${xml.knowledge_entry(entry)}
        ${xml.separator() if not loop.last else ""}
    % endfor
</knowledge_base>
% endif
