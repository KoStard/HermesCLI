<%namespace name="xml" file="/macros/xml.mako"/>
${'##'} Criteria of Definition of Done
% if not criteria:
No criteria defined yet.
% else:
% for i, (criterion, done) in enumerate(zip(criteria, criteria_done)):
${i+1}. [${u'✓' if done else ' '}] ${criterion}
% endfor
% endif
