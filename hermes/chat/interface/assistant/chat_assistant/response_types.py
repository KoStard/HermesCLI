class BaseLLMResponse:
    pass


class ThinkingLLMResponse(BaseLLMResponse):
    def __init__(self, text: str):
        self.text = text


class TextLLMResponse(BaseLLMResponse):
    def __init__(self, text: str):
        self.text = text
