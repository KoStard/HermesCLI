import os


class FileCleaner:
    @staticmethod
    def cleanup(file_path: str):
        if os.path.exists(file_path):
            os.remove(file_path)
