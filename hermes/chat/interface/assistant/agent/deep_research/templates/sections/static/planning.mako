<%namespace name="xml" file="/macros/xml.mako"/>

${'##'} Parallel Planning Strategy

When processing requests:
1. **Identify Parallel Opportunities**: Look for independent tasks that can run concurrently
2. **Batch Commands**: Group non-dependent commands in single messages
3. **Async Activation**: Use `activate_subproblems` early to start parallel processing
4. **Selective Waiting**: Use `wait_for_subproblems` only when outputs are needed

Workflow patterns:
- **Parallel Discovery**: Activate multiple research subproblems simultaneously
- **Mixed Workloads**: Combine local commands with parallel subproblems
- **Budget-aware Batching**: Group commands based on estimated resource costs
- If you have previously executed commands, ask yourself in your writing, do you see the effects of your commands? Maybe they didn't get executed because of wrong structure? There is a report showing the executed commands, errors, etc.
