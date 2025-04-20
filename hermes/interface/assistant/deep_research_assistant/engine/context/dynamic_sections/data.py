from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any, Sequence, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular imports at runtime
if TYPE_CHECKING:
    from hermes.interface.assistant.deep_research_assistant.engine.files.file_system import Node, Artifact, FileSystem
    from hermes.interface.assistant.deep_research_assistant.engine.files.knowledge_entry import KnowledgeEntry


@dataclass(frozen=True)
class DynamicSectionData:
    """Base class for dynamic section data. Frozen makes instances hashable."""
    pass


# --- Concrete Data Classes for Each Section ---

@dataclass(frozen=True)
class HeaderSectionData(DynamicSectionData):
    # Header is static text defined in its template, no data needed from context
    pass


@dataclass(frozen=True)
class PermanentLogsData(DynamicSectionData):
    permanent_logs: List[str]


@dataclass(frozen=True)
class BudgetSectionData(DynamicSectionData):
    budget: Optional[int]
    remaining_budget: Optional[int]


# --- Primitive Data Structures for Complex Objects ---
# These are used within the main data classes below

@dataclass(frozen=True)
class PrimitiveArtifactData:
    """Immutable, primitive representation of an Artifact for comparison."""
    name: str
    content: str
    is_external: bool
    is_fully_visible: bool # Added to track visibility state directly
    owner_title: Optional[str] = None # Added to track ownership for node artifacts

    @staticmethod
    def from_artifact(artifact: "Artifact", owner_title: Optional[str] = None, is_fully_visible: bool = True) -> "PrimitiveArtifactData":
        return PrimitiveArtifactData(
            name=artifact.name,
            content=artifact.content,
            is_external=artifact.is_external,
            is_fully_visible=is_fully_visible,
            owner_title=owner_title
        )

@dataclass(frozen=True)
class PrimitiveSubproblemData:
    """Immutable, primitive representation of a Node's subproblem summary."""
    # Fields needed for summary rendering parity
    title: str
    problem_definition: str
    criteria: Tuple[str, ...]
    criteria_done: Tuple[bool, ...]
    artifacts_count: int
    status_emoji: str
    status_label: str
    criteria_status: str # Combined criteria met/total string

    @staticmethod
    def from_node(node: "Node") -> "PrimitiveSubproblemData":
        return PrimitiveSubproblemData(
            title=node.title,
            problem_definition=node.problem_definition,
            criteria=tuple(node.criteria),
            criteria_done=tuple(node.criteria_done),
            artifacts_count=len(node.artifacts),
            status_emoji=node.get_status_emoji(),
            status_label=node.get_status_label(),
            criteria_status=node.get_criteria_status()
        )

@dataclass(frozen=True)
class PrimitiveNodePathData:
    """Immutable, primitive representation of a Node in a hierarchy path."""
    # Fields needed for path rendering parity
    title: str
    problem_definition: str
    criteria: Tuple[str, ...]
    criteria_done: Tuple[bool, ...]
    artifacts_count: int
    depth: int
    is_current: bool
    # Include sibling subproblems not in the direct path
    sibling_subproblems: Tuple[PrimitiveSubproblemData, ...] = field(default_factory=tuple)

    @staticmethod
    def from_node(
        node: "Node",
        is_current: bool,
        sibling_subproblems_data: Tuple[PrimitiveSubproblemData, ...] = ()
    ) -> "PrimitiveNodePathData":
        return PrimitiveNodePathData(
            title=node.title,
            problem_definition=node.problem_definition,
            criteria=tuple(node.criteria),
            criteria_done=tuple(node.criteria_done),
            artifacts_count=len(node.artifacts),
            depth=node.depth_from_root,
            is_current=is_current,
            sibling_subproblems=sibling_subproblems_data
        )

@dataclass(frozen=True)
class PrimitiveKnowledgeEntryData:
    """Immutable, primitive representation of a KnowledgeEntry."""
    content: str
    author_node_title: str
    timestamp: str
    title: Optional[str]
    tags: Tuple[str, ...] # Use tuple for immutability

    @staticmethod
    def from_entry(entry: "KnowledgeEntry") -> "PrimitiveKnowledgeEntryData":
        return PrimitiveKnowledgeEntryData(
            content=entry.content,
            author_node_title=entry.author_node_title,
            timestamp=entry.timestamp,
            title=entry.title,
            tags=tuple(entry.tags) # Convert list to tuple
        )


# --- Main Dynamic Section Data Classes (using primitives) ---

@dataclass(frozen=True)
class ArtifactsSectionData(DynamicSectionData):
    # Store primitive representations
    external_files: Tuple[PrimitiveArtifactData, ...] = field(default_factory=tuple)
    node_artifacts: Tuple[PrimitiveArtifactData, ...] = field(default_factory=tuple)

    @staticmethod
    def from_artifact_lists(
        external_files_dict: Dict[str, "Artifact"],
        node_artifacts_list: List[Tuple[str, str, str, bool]] # (owner_title, name, content, is_fully_visible)
    ) -> "ArtifactsSectionData":
        # Convert external files dict to primitive tuple
        external_primitives = tuple(
            PrimitiveArtifactData.from_artifact(artifact, is_fully_visible=True) # External are always visible
            for name, artifact in sorted(external_files_dict.items()) # Sort for consistent order
        )

        # Convert node artifacts list to primitive tuple
        node_primitives = tuple(
            PrimitiveArtifactData(
                name=name,
                content=content,
                is_external=False, # Node artifacts are not external
                is_fully_visible=is_fully_visible,
                owner_title=owner_title
            )
            for owner_title, name, content, is_fully_visible in sorted(node_artifacts_list, key=lambda x: (x[0], x[1])) # Sort
        )

        return ArtifactsSectionData(
            external_files=external_primitives,
            node_artifacts=node_primitives
        )


@dataclass(frozen=True)
class ProblemHierarchyData(DynamicSectionData):
    # Store only the pre-rendered string and target node title
    file_system_hierarchy_str: str
    target_node_title: str

    @staticmethod
    def from_filesystem_and_node(fs: "FileSystem", target_node: "Node") -> "ProblemHierarchyData":
        hierarchy_str = fs.get_problem_hierarchy(target_node)
        return ProblemHierarchyData(
            file_system_hierarchy_str=hierarchy_str,
            target_node_title=target_node.title
        )

@dataclass(frozen=True)
class CriteriaSectionData(DynamicSectionData):
    # These are already primitive, just add factory
    criteria: Tuple[str, ...]
    criteria_done: Tuple[bool, ...]

    @staticmethod
    def from_node(target_node: "Node") -> "CriteriaSectionData":
        return CriteriaSectionData(
            criteria=tuple(target_node.criteria),
            criteria_done=tuple(target_node.criteria_done)
        )

@dataclass(frozen=True)
class SubproblemsSectionData(DynamicSectionData):
    # Store primitive representations of subproblems
    subproblems: Tuple[PrimitiveSubproblemData, ...]

    @staticmethod
    def from_node(target_node: "Node") -> "SubproblemsSectionData":
        subproblem_data = tuple(
            PrimitiveSubproblemData.from_node(subproblem)
            for title, subproblem in sorted(target_node.subproblems.items()) # Sort for consistent order
        )
        return SubproblemsSectionData(subproblems=subproblem_data)


@dataclass(frozen=True)
class ProblemPathHierarchyData(DynamicSectionData):
    # Store primitive representations of nodes in the path
    path_nodes: Tuple[PrimitiveNodePathData, ...]

    @staticmethod
    def from_parent_chain(parent_chain: List["Node"], current_node: "Node") -> "ProblemPathHierarchyData":
        path_data_list = []
        for i, node in enumerate(parent_chain):
            is_current_node_in_path = (node == current_node)
            next_node_in_path = parent_chain[i + 1] if i + 1 < len(parent_chain) else None

            # Collect data for sibling subproblems (those not the next node in the path)
            sibling_data = []
            for sub_title, sub_node in sorted(node.subproblems.items()):
                if sub_node != next_node_in_path:
                    sibling_data.append(PrimitiveSubproblemData.from_node(sub_node))

            # Create the PrimitiveNodePathData including siblings
            node_path_data = PrimitiveNodePathData.from_node(
                node=node,
                is_current=is_current_node_in_path,
                sibling_subproblems_data=tuple(sibling_data)
            )
            path_data_list.append(node_path_data)

        return ProblemPathHierarchyData(path_nodes=tuple(path_data_list))


@dataclass(frozen=True)
class KnowledgeBaseData(DynamicSectionData):
    # Store primitive representations of knowledge entries
    knowledge_entries: Tuple[PrimitiveKnowledgeEntryData, ...]

    @staticmethod
    def from_knowledge_base(knowledge_base: List["KnowledgeEntry"]) -> "KnowledgeBaseData":
        entry_data = tuple(
            PrimitiveKnowledgeEntryData.from_entry(entry)
            # Sort by timestamp descending for consistent order (newest first)
            for entry in sorted(knowledge_base, key=lambda x: x.timestamp, reverse=True)
        )
        return KnowledgeBaseData(knowledge_entries=entry_data)


@dataclass(frozen=True)
class GoalSectionData(DynamicSectionData):
    # Goal is static text defined in its template, no data needed from context
    pass
