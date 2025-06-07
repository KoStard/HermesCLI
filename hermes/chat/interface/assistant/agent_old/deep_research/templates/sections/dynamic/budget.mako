<%namespace name="xml" file="/macros/xml.mako"/>
<%
budget_status = "GOOD"
if budget is not None and remaining_budget is not None:
    if remaining_budget <= 0:
        budget_status = "CRITICAL"
    elif remaining_budget <= 10:
        budget_status = "LOW"
%>
${'#'} Budget Information
% if budget is None or remaining_budget is None:
No budget has been set.
% else:
- Total budget: ${budget} message cycles
- Used: ${budget - remaining_budget} message cycles
- Remaining: ${remaining_budget} message cycles
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
