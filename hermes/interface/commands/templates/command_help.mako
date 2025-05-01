% for name, cmd in sorted(commands.items()):
<<< ${name}
%   for section in cmd.sections:
///${section.name + (" (multiple allowed)" if section.allow_multiple else "")}
%     if section.help_text:
${section.help_text}
%     else:
Your ${section.name} here
%     endif
%   endfor
>>>
%   if cmd.help_text:
%     for line in cmd.help_text.split("\n"):
; ${line}
%     endfor
%   endif

% endfor
