## Context:
## - criteria_list: Tuple[str]
## - criteria_done_list: Tuple[bool]
<%namespace name="xml" file="/macros/xml.mako"/>
${'##'} Criteria of Definition of Done
% if not criteria_list:
No criteria defined yet.
% else:
% for i, (criterion, done) in enumerate(zip(criteria_list, criteria_done_list)):
${i+1}. [${u'✓' if done else ' '}] ${criterion}
% endfor
% endif
