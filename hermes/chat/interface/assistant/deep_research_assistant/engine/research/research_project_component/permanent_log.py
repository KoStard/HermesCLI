from datetime import datetime


class NodePermanentLogs:
    """Maintains a log of permanent entries for the research project"""
    
    def __init__(self):
        self._logs = []
    
    def add_log(self, content: str) -> None:
        """Add a new log entry with timestamp"""
        timestamp = datetime.now().isoformat()
        self._logs.append(f"[{timestamp}] {content}")
    
    def get_logs(self) -> list[str]:
        """Get all logs"""
        return self._logs.copy()
