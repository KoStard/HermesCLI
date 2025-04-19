<%! from typing import List, Optional %>
<%namespace name="xml" file="/macros/xml.mako"/>

% if static_content:
${static_content}
% endif

% if dynamic_sections:
% for section in dynamic_sections:
${section}
% endfor
% endif
