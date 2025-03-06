import logging


class DocstringModelStrategy:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def check_outdated(
        self, code_generation_input: str, existing_docstring: str
    ) -> bool:
        raise NotImplementedError()

    def generate_docstring(self, code_generation_input: str) -> dict:
        raise NotImplementedError()
