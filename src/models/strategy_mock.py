from random import randint

from gpt_input import (
    GptInputClassObject,
    GptInputCodeObject,
    GptInputMethodObject,
    GptInputModuleObject,
    GptOutput,
    GptOutputClass,
    GptOutputMethod,
    GptOutputModule,
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
        if randint(0, 6) == 0:
            description = False
        else:
            description = "MOCK This is a docstring description."

        if isinstance(code_object, GptInputMethodObject) or isinstance(
            code_object, GptInputModuleObject
        ):
            exception_descriptions = {}
            for exception in code_object.exceptions:
                if randint(0, 6) == 0:
                    exception_descriptions[exception] = False
                else:
                    exception_descriptions[exception] = "MOCK exception description"

        if isinstance(code_object, GptInputMethodObject):
            return_type = None
            if code_object.return_missing:
                if randint(0, 6) == 0:
                    return_type = False
                else:
                    return_type = "MOCK return type"

            param_types = {}
            for param_name in code_object.parameters:
                if randint(0, 6) == 0:
                    param_types[param_name] = False
                else:
                    param_types[param_name] = "MOCK type"

            param_descriptions = {}
            for param_name in code_object.parameters:
                if randint(0, 6) == 0:
                    param_descriptions[param_name] = False
                else:
                    param_descriptions[param_name] = "MOCK description for this parameter"

            if randint(0, 6) == 0:
                return_description = False
            else:
                return_description = "MOCK return description"

            return GptOutputMethod(
                id=code_object.id,
                no_change_necessary=False,
                description=description,
                parameter_types=param_types,
                parameter_descriptions=param_descriptions,
                exception_descriptions=exception_descriptions,
                return_description=return_description,
                return_type=return_type,
                validationerror=False,
                generationerror=False,
            )
        elif isinstance(code_object, GptInputClassObject):
            class_attribute_types = {}
            for attr in code_object.class_attributes:
                if randint(0, 6) == 0:
                    class_attribute_types[attr["name"]] = False
                else:
                    class_attribute_types[attr["name"]] = "MOCK type"

            class_attribute_descriptions = {}
            for attr in code_object.class_attributes:
                if randint(0, 6) == 0:
                    class_attribute_descriptions[attr["name"]] = False
                else:
                    class_attribute_descriptions[attr["name"]] = "MOCK class attr description"

            instance_attribute_types = {}
            for attr in code_object.instance_attributes:
                if randint(0, 6) == 0:
                    instance_attribute_types[attr["name"]] = False
                else:
                    instance_attribute_types[attr["name"]] = "MOCK type"

            instance_attribute_descriptions = {}
            for attr in code_object.instance_attributes:
                if randint(0, 6) == 0:
                    instance_attribute_descriptions[attr["name"]] = False
                else:
                    instance_attribute_descriptions[attr["name"]] = (
                        "MOCK class instance description"
                    )

            return GptOutputClass(
                id=code_object.id,
                no_change_necessary=False,
                description=description,
                class_attribute_descriptions=class_attribute_descriptions,
                class_attribute_types=class_attribute_types,
                instance_attribute_descriptions=instance_attribute_descriptions,
                instance_attribute_types=instance_attribute_types,
                validationerror=False,
                generationerror=False,
            )
        elif isinstance(code_object, GptInputModuleObject):
            return GptOutputModule(
                id=code_object.id,
                no_change_necessary=False,
                description=description,
                exception_descriptions=exception_descriptions,
                validationerror=False,
                generationerror=False,
            )
