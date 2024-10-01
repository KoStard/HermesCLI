import unittest
from unittest.mock import Mock
from hermes.chat_models.base import ChatModel

class TestChatModel(unittest.TestCase):
    def test_init_sets_config_and_model_tag(self):
        config = {"key": "value"}
        model_tag = "test_model"
        chat_model = Mock(spec=ChatModel)
        chat_model.config = config
        chat_model.model_tag = model_tag
        self.assertEqual(chat_model.config, config)
        self.assertEqual(chat_model.model_tag, model_tag)

    def test_initialize_raises_not_implemented(self):
        chat_model = Mock(spec=ChatModel)
        chat_model.initialize.side_effect = NotImplementedError()
        with self.assertRaises(NotImplementedError):
            chat_model.initialize()

    def test_send_history_raises_not_implemented(self):
        chat_model = Mock(spec=ChatModel)
        chat_model.send_history.side_effect = NotImplementedError()
        with self.assertRaises(NotImplementedError):
            next(chat_model.send_history([]))

if __name__ == '__main__':
    unittest.main()
