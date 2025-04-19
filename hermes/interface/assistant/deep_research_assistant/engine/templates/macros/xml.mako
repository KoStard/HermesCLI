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