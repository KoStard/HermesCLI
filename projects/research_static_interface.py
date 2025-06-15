from pathlib import Path

from hermes.chat.interface.templates.template_manager import TemplateManager

path = Path(__file__).parent.parent / "hermes/chat/interface/assistant/deep_research/templates/"
template_manager = TemplateManager(path)
print(template_manager.render_template("research_static.mako", commands_help_content="{{commands_help_content}}"))
