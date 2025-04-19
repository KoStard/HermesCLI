<%namespace name="xml" file="/macros/xml.mako"/>

% if not external_files and not node_artifacts:
<artifacts>
No artifacts available.
</artifacts>
% else:
<artifacts>
    % if external_files:
    <external_files_intro>
    These are external files provided by the user at the start of this research. They contain important context for the problem and are always fully available.
    </external_files_intro>

    % for name, artifact in sorted(external_files.items()):
    ${xml.artifact(name, artifact.content, type="external_file")}
    % endfor

    % if node_artifacts:
    ${xml.separator()}

    <node_artifacts_intro>
    These are artifacts created during the research process within specific problems.
    </node_artifacts_intro>
    % endif
    % endif

    % if node_artifacts:
    % for owner_title, name, content, is_fully_visible in sorted(node_artifacts, key=lambda x: (x[0], x[1])):
    ${xml.artifact(name, content if is_fully_visible else truncator.truncate(content, 500, "Use 'open_artifact' command to view full content."), owner=owner_title)}
    % endfor
    % endif
</artifacts>
% endif
