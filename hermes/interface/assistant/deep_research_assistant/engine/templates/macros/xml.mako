<%def name="section(name, content='')">
<${name}>
${content}
</${name}>
</%def>

<%def name="artifact(name, content, **attrs)">
<artifact name="${name}"${' '.join(f' {k}="{v}"' for k, v in attrs.items())}>
${content}
</artifact>
</%def>

<%def name="separator()">
<separator>---------------------</separator>
</%def>

<%def name="node(title, content, **attrs)">
<node title="${title}"${' '.join(f' {k}="{v}"' for k, v in attrs.items())}>
${content}
</node>
</%def>

<%def name="problem_definition(content)">
<problem_definition>
  ${content}
</problem_definition>
</%def>

<%def name="criterion(content, status)">
<criterion status="${status}">
${content}
</criterion>
</%def>
