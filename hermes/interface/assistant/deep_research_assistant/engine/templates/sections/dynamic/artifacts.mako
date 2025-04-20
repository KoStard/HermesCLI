## Context:
## - external_files_data: Tuple[PrimitiveArtifactData]
## - node_artifacts_data: Tuple[PrimitiveArtifactData]
## - truncator: ContentTruncator class
<%namespace name="xml" file="/macros/xml.mako"/>
${'#'} Artifacts (All Problems)

% if not external_files_data and not node_artifacts_data:
<artifacts>
No artifacts available.
</artifacts>
% else:
<artifacts>
    % if external_files_data:
    <external_files_intro>
    These are external files provided by the user at the start of this research. They contain important context for the problem and are always fully available.
    </external_files_intro>

    % for artifact_data in external_files_data: ## Already sorted by factory method
    ${xml.artifact(artifact_data.name, artifact_data.content, type="external_file")}
    % endfor

    % if node_artifacts_data:
    ${xml.separator()}

    <node_artifacts_intro>
    These are artifacts created during the research process within specific problems.
    </node_artifacts_intro>
    % endif
    % endif

    % if node_artifacts_data:
    % for artifact_data in node_artifacts_data: ## Already sorted by factory method
    ${xml.artifact(
        artifact_data.name,
        artifact_data.content if artifact_data.is_fully_visible else truncator.truncate(artifact_data.content, 500, "Use 'open_artifact' command to view full content."),
        owner=artifact_data.owner_title
    )}
    % endfor
    % endif
</artifacts>
% endif
