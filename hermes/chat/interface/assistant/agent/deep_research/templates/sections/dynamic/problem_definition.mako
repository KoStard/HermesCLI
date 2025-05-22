<%namespace name="xml" file="/macros/xml.mako"/>

${'##'} Problem Details

${'###'} The problem assigned to you

Notice that the problem assigned to you doesn't change during the whole chat.

Title: "${title}"
% if depth > 3:
⚠️ **DEPTH WARNING**
You are currently at depth level ${depth}, which exceeds the recommended maximum of 3 levels.
Please avoid creating additional subproblems at this level. Instead:
1. Try to solve the current problem directly
2. Use `finish_problem` to allow the parent problem to resume
3. If necessary, mark the current problem as failed using `fail_problem` command

Excessive depth makes the problem hierarchy difficult to manage and can lead to scope creep.
% endif

${'###'} Problem Definition
${content}