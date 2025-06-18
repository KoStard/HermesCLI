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
    ${xml.artifact(artifact_data.name, artifact_data.content, type="external_file", is_open="true")}
    % endfor

    % if node_artifacts_data:
    ${xml.separator()}

    <node_artifacts_intro>
    These are artifacts created during the research process within specific problems. By default, artifacts are closed and show only their summary. Use the open_artifact command to view full content. Each artifact should be approximately 1 page long unless specifically requested to be longer. Artifact names should clearly indicate their purpose. Opened artifacts will automatically close after 5 message iterations to keep the interface manageable.
    </node_artifacts_intro>
    % endif
    % endif

    % if node_artifacts_data:
    % for artifact_data in node_artifacts_data: ## Already sorted by factory method
    ${xml.artifact(
        artifact_data.name,
        artifact_data.content if artifact_data.is_fully_visible else "Summary: " + artifact_data.short_summary,
        owner=artifact_data.owner_title,
        is_open=artifact_data.is_fully_visible,
    )}
    % endfor
    % endif
</artifacts>
% endif
