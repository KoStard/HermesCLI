from datetime import datetime

from hermes.chat.interface.assistant.models.prompt_builder.base import PromptBuilderFactory


class TextMessagesAggregator:
    def __init__(self, prompt_builder_factory: PromptBuilderFactory):
        self.prompt_builder_factory = prompt_builder_factory
        self.messages = []

    def add_message(
        self,
        *,
        message: str,
        author: str,
        message_id: int,
        name: str | None = None,
        text_role: str | None = None,
    ):
        if message:
            msg = {"role": author, "content": message}
            if name:
                msg["name"] = name
            if text_role:
                msg["text_role"] = text_role
            if author == "user":
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                msg["content"] = f"[{current_time}] {msg['content']}"
            self.messages.append(msg)

    def get_current_author(self) -> str | None:
        if not self.messages:
            return None
        return self.messages[-1]["role"]

    def is_empty(self) -> bool:
        return not self.messages

    def compile_request(self) -> str:
        if self.is_empty():
            return ""

        if self.get_current_author() != "user":
            return "\n".join([message["content"] for message in self.messages])

        prompt_builder = self.prompt_builder_factory.create_prompt_builder()

        for message in self.messages:
            prompt_builder.add_text(
                text=message["content"],
                name=message.get("name"),
                text_role=message.get("text_role"),
            )
        return prompt_builder.compile_prompt()

    def clear(self):
        self.messages = []
