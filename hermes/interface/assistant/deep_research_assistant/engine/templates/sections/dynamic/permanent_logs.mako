<%namespace name="xml" file="/macros/xml.mako"/>
<%
# Receive raw logs and format them here
formatted_logs = ("\n".join(f"- {entry}" for entry in permanent_logs)
                  if permanent_logs
                  else "No history entries yet.")
%>
${'#'} Permanent Logs
${xml.section('permanent_log', formatted_logs)}
