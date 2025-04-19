<%namespace name="xml" file="/macros/xml.mako"/>
======================
${'#'} Budget Information
% if total is None or remaining is None:
No budget has been set.
% else:
- Total budget: ${total} message cycles
- Used: ${total - remaining} message cycles
- Remaining: ${remaining} message cycles
- Status: ${budget_status}

% if budget_status == "CRITICAL":
⚠️ **BUDGET CRITICAL** ⚠️
You are operating on borrowed time. Please finalize your work immediately and submit your findings.
% elif budget_status == "LOW":
⚠️ **BUDGET WARNING** ⚠️
Budget is running low. Please prioritize the most important tasks and consider wrapping up soon.
% else:
Please be mindful of the budget when planning your research strategy.
% endif
% endif
