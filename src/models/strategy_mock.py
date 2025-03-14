from gpt_input import (
    GptInputClassObject,
    GptInputCodeObject,
    GptInputMethodObject,
    GptOutput,
    GptOutputMethod,
)

from .model_strategy import DocstringModelStrategy


class MockStrategy(DocstringModelStrategy):
    def __init__(self):
        super().__init__()

        self.change_necessary = False

        self.logger.info("Using mock strategy")

    def check_outdated(self, code_object: GptInputCodeObject) -> bool:
        self.change_necessary = not self.change_necessary
        return self.change_necessary

    def generate_docstring(self, code_object: GptInputCodeObject) -> GptOutput:
        if isinstance(code_object, GptInputMethodObject):
            return_type = None
            if code_object.return_missing:
                return_type = "MOCK return type"

            return GptOutputMethod(
                id=code_object.id,
                no_change_necessary=False,
                description="MOCK This is a docstring description.",
                parameter_types={
                    name: "MOCK type" for name in code_object.missing_parameters
                },
                parameter_descriptions={
                    param["name"]: "MOCK description for this parameter"
                    for param in code_object.parameters
                },
                exception_descriptions={
                    exception: "MOCK exception description"
                    for exception in code_object.exceptions
                },
                return_description="MOCK return type description",
                return_missing=code_object.return_missing,
                return_type=return_type,
            )
        elif isinstance(code_object, GptInputClassObject):
            return GptOutput(
                id=code_object.id,
                no_change_necessary=False,
                description="MOCK This is a docstring description.",
            )
        else:
            raise NotImplementedError
