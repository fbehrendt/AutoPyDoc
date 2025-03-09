import logging

from gpt_input import GptInputCodeObject, GptOutput


class DocstringModelStrategy:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def check_outdated(self, code_object: GptInputCodeObject) -> bool:
        raise NotImplementedError()

    def generate_docstring(self, code_object: GptInputCodeObject) -> GptOutput:
        raise NotImplementedError()
