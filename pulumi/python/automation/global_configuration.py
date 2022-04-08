import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class GlobalConfiguration:
    @staticmethod
    def path() -> str:
        relative_path = os.path.sep.join([SCRIPT_DIR, '..', '..', '..', 'config', 'environment'])
        absolute_path = os.path.abspath(relative_path)
        return os.path.normpath(absolute_path)
