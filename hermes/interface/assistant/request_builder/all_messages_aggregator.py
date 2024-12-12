class AllMessagesAggregator:
    """
    With add_message(message, author) method, lots of messages are added to the aggregator.
    With get_aggregated_messages() method, [([message, ...], author), ...] is returned, grouping sequential messages by author.
    """
    
    def __init__(self):
        self._message_pairs = []

    def add_message(self, message, author):
        """
        Add a message with its author to the aggregator.
        
        Args:
            message: The message content
            author: The author of the message
        """
        self._message_pairs.append((message, author))

    def get_aggregated_messages(self):
        """
        Returns a list of tuples, where each tuple contains:
        - A list of sequential messages from the same author
        - The author of those messages
        
        Returns:
            List[Tuple[List[Any], str]]: List of (messages, author) tuples
        """
        if not self._message_pairs:
            return []

        result = []
        current_messages = [self._message_pairs[0][0]]
        current_author = self._message_pairs[0][1]

        for message, author in self._message_pairs[1:]:
            if author == current_author:
                current_messages.append(message)
            else:
                result.append((current_messages, current_author))
                current_messages = [message]
                current_author = author

        # Add the last group
        result.append((current_messages, current_author))

        return result