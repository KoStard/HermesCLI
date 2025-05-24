# Permanent Researchers System Design

## Problem Statement

The current Deep Research system is designed for one-off research sessions. We want to create a permanent researchers system where:

1. Each project folder maintains persistent research context
2. Multiple research sessions can be created and reactivated
3. Knowledge base is shared across all research sessions in a project
4. Root node serves as project summary, not an active research problem
5. Multiple concurrent sessions are supported

## Current vs Target Architecture

### Current System
```
Research Session
├── Root Node (has problem definition)
│   ├── Subproblem 1
│   ├── Subproblem 2
│   └── Knowledge Base (shared)
```

### Target System
```
Project Folder
├── Root Node (project summary only)
│   ├── Knowledge Base (shared across all researchers)
│   ├── Researcher 1 (active research problem)
│   ├── Researcher 2 (active research problem)
│   ├── Researcher 3 (completed research problem)
│   └── ...
```

## Key Changes

### 1. Root Node Transformation
- **Current**: Root node has problem definition and can be actively researched
- **Target**: Root node contains only:
  - Project summary/goal
  - Shared knowledge base
  - List of all researchers (first-level children)
  - Project-level artifacts

### 2. Knowledge Base Sharing
- **Current**: Knowledge base scoped to entire research project
- **Target**: Knowledge base remains at root level, accessible by all researchers

### 3. Research Session Management
- **Current**: Single research session per root problem
- **Target**: Multiple researchers (first-level children) can be:
  - Created fresh
  - Reactivated from previous state
  - Run concurrently in different terminal sessions

### 4. Finish Node Behavior
- **Current**: `finish_node` can reach root level
- **Target**: `finish_node` stops at first child level (researcher level)

### 5. User Commands
- **Current**: Direct problem definition at root
- **Target**: New user commands:
  - `/research create <name>` - Create new researcher
  - `/research activate <name>` - Reactivate existing researcher
  - `/research list` - List all researchers and their status
  - These should send events to the deep research engine, which should make the necessary changes, so new events are required.

## Implementation Plan

### Phase 1: Core Architecture Changes

1. **Update Root Node Structure**
   - Remove problem definition requirement from root nodes
   - Add project summary field
   - Update root node initialization in `AgentEngine`

2. **Create Researcher Management System**
   - New `ResearcherManager` class
   - Commands to create/activate researchers
   - Status tracking for researchers

3. **Update Finish Node Logic**
   - Modify `finish_problem` command to detect first-level children
   - Prevent finishing beyond researcher level

### Phase 2: Context Generation Updates

4. **Update Context Templates**
   - Root node context shows project summary + researcher list
   - Researcher context includes root summary + shared knowledge base
   - New researcher gets fresh history but sees shared artifacts

5. **File System Organization**
   ```
   project_root/
   ├── Results/
   │   ├── project_artifacts.md
   │   ├── Researcher_1/
   │   │   └── artifacts...
   │   └── Researcher_2/
   │       └── artifacts...
   └── Research/
       ├── project_summary.md
       ├── _knowledge_base.md (shared)
       ├── researchers_status.json
       ├── Researcher_1/
       │   ├── Problem Definition.md
       │   ├── history.json
       │   └── Subproblems/...
       └── Researcher_2/
           ├── Problem Definition.md
           ├── history.json
           └── Subproblems/...
   ```

### Phase 3: User Interface Integration

6. **Add User Commands**
   - Integrate with existing command system
   - Add help text and validation
   - Handle concurrent access gracefully

## Technical Considerations

### Concurrent Access
- Multiple terminal sessions may access same project
- File-based coordination through status files
- Lock-free design using atomic operations where possible

### State Management
- Each researcher maintains independent history
- Shared knowledge base requires careful write coordination
- Project summary updated when researchers complete

### Backwards Compatibility
- No backwards compatibility needed

## Implementation Details

### New Classes Required

1. **`ProjectManager`** - Manages project-level state
2. **`ResearcherRegistry`** - Tracks active/inactive researchers
3. **`SharedKnowledgeBase`** - Handles concurrent access to KB
4. **User Commands** - Create/activate/list researchers

### Modified Classes

1. **`AgentEngine`** - Handle root vs researcher initialization
2. **`ResearchNode`** - Support project summary mode
3. **`FinishProblemCommand`** - Detect researcher boundary
4. **Context templates** - Updated for new hierarchy

### File Format Changes

1. **`researchers_status.json`** - Track researcher states
2. **`project_summary.md`** - Project-level description
3. **Updated directory structure** - Researcher-based organization

## Benefits

1. **Persistent Context**: Research context survives across sessions
2. **Knowledge Accumulation**: Shared knowledge base grows over time
3. **Parallel Research**: Multiple research tracks in same project
4. **Session Management**: Easy to switch between research problems
5. **Collaboration**: Multiple users can work on different researchers

## Risks & Mitigation

1. **File Conflicts**: Mitigate with careful file organization and status tracking
2. **Knowledge Base Corruption**: Implement backup and recovery mechanisms
3. **Complex State Management**: Clear separation of concerns and well-defined interfaces
4. **Migration Complexity**: Provide clear migration path and validation

## Next Steps

1. Implement core architecture changes
2. Update templates and context generation
3. Add user commands and integration
4. Test with concurrent sessions
5. Create migration tools for existing projects
