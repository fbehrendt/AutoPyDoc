import logging
import re
from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from code_representation import ContextObject

import json5
from gpt4all import GPT4All

import gpt_input
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
from save_data import save_data

from .model_factory import ModelStrategyFactory
from .model_strategy import DocstringModelStrategy

CHECK_OUTDATED_JSON_OUTPUT_REGEX = (
    r'({\s*"analysis":\s*"(.*)"\s*,\s*"matches"\s*:\s*(true|false)\s*})'
)
DOCSTRING_GENERATION_JSON_OUTPUT_REGEX = r"{[^`]+}"


class DeepseekR1PromptBuilder:
    def __init__(self, context_size: int):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.context_size = context_size

        self.check_outdated_prompt_template = """
You are an AI documentation assistant, and your task is to evaluate if an existing docstring for {code_type} {code_name} correctly describes the given code of the function.
The purpose of the documentation is to help developers and beginners understand the code and its specific usage.

The docstring has to pass all of the following criteria to pass:
- concise description
- description accurately describes what the code does (rather than how)
- all class and instance attributes are described
- all exception raised directly (rather than in an method/subclass within the class) are described
- docstring is not a mock

Criteria not mentioned above shall not be considered! Especially, methods and subclasses do not have to be described and no examples have to be (but can be) included

The code looks like the following:
<code>
{code}
</code>

The existing docstring is as follows:
<existing-docstring>
{existing_docstring}
</existing-docstring>

The context of the code is as follows:
{context}

Reason step by step to find out if the existing docstring matches the code, and put your final answer within <output-format syntax="json">{{
    "analysis": "<your_analysis_goes_here>",
    "matches": <true | false>
}}
</output-format>

<think>
"""

        self.generate_method_docstring_prompt_template = """
You are an AI documentation assistant, and your task is to analyze the code of a Python function called {code_name}.
The purpose of the analysis is to help developers and beginners understand the function and specific usage of the code.
Use plain text (including all details), in a deterministic tone.

The code looks like the following:
<code>
{code}
</code>

The context of the function is as follows:
{context}

Please note:
- Write mainly in the english language. If necessary, you can write with some English words in the analysis and description to enhance the document's readability because you do not need to translate the function name or variable name into the target language.
- Keep the text short and concise, and avoid unnecessary details.
- Keep in mind that your audience is document readers, so use a deterministic tone to generate precise content and don't let them know you're provided with code snippet and documents.
- AVOID ANY SPECULATION and inaccurate descriptions!
- DO NOT use markdown syntax in the output

Now, provide the documentation for the target object in english in a professional way.
Please reason step by step, and always summarize your final answer using the following json format <output-format syntax="json">{{
    "description": "<docstring_description>",
    "parameters": [
        {{"name": "<parameter_name_1>", "type": "<parameter_type_1>", "description": "<description_for_parameter_1>"}},
        {{"name": "<parameter_name_2>", "type": "<parameter_type_2>", "description": "<description_for_parameter_2>"}},
        // ... more parameters as needed
    ],
    "returns": {{"type": "<return_type>", "description": "<description_for_return_value>"}}
}}</output-format>. Stick to this format WITHOUT EXCEPTIONS and write valid json with quoted fields.

Here is an example of the expected output format:
<output-example syntax="json">
{{"description": "Extract start, end and content of methods affected by change information",
    "parameters": [
        {{
            "name": "filename",
            "type": "str",
            "description": "File to extract method information from"
        }},
        {{
            "name": "change_start",
            "type": "int",
            "description": "Line where the change begins"
        }},
        {{
            "name": "change_length",
            "type": "int",
            "description": "Line length of the change"
        }}
    ],
    "returns": {{
        "type": "list[dict[str|int]]",
        "description": "list of method information as dict with keys type, filename, start, end, content"
    }}
}}
</output-example>

<think>
"""

        self.generate_class_docstring_prompt_template = """
You are an AI documentation assistant, and your task is to analyze the code of a Python class called {code_name}. The output will be used to construct a new docstring.
The purpose of the analysis is to help developers and beginners understand the class and specific usage of the code.
Use plain text (including all details), in a deterministic tone. Provided context shall be used to better understand what the class does and does not need to be analyzed further than that. Do not generate descriptions for methods and subclasses.

The code looks like the following:
<code>
{code}
</code>

The context of the class is as follows:
{context}

Please note:
- Write mainly in the english language. If necessary, you can write with some English words in the analysis and description to enhance the document's readability because you do not need to translate the function name or variable name into the target language.
- Keep the text short and concise, and avoid unnecessary details.
- Keep in mind that your audience is document readers, so use a deterministic tone to generate precise content and don't let them know you're provided with code snippet and documents.
- AVOID ANY SPECULATION and inaccurate descriptions!
- DO NOT use markdown syntax in the output

Now, provide the documentation for the target object in english in a professional way.
Please reason step by step, and always summarize your final answer using the following json format <output-format syntax="json">{{
    "description": "<docstring_description>",
    "class_attributes": [
        {{"name": "<class_attribute_name_1>", "type": "<class_attribute_type_1>", "description": "<description_for_class_attribute_1>"}}
        // ... more class attributes as needed
    ],
    "instance_attributes": [
        {{"name": "<instance_attribute_name_1>", "type": "<instance_attribute_type_1>", "description": "<description_for_instance_attribute_1>"}}
        // ... more instance attribute as needed
    ]
}}</output-format>. Stick to this format WITHOUT EXCEPTIONS and write valid json with quoted fields.

<think>
"""
        # TODO: add example back

        self.generate_module_docstring_prompt_template = """
You are an AI documentation assistant, and your task is to analyze the code of a Python module.
The purpose of the analysis is to help developers and beginners understand the module and specific usage of the code.
Use plain text (including all details), in a deterministic tone.

The code looks like the following:
<code>
{code}
</code>

The context of the module is as follows:
{context}

Please note:
- Write mainly in the english language. If necessary, you can write with some English words in the analysis and description to enhance the document's readability because you do not need to translate the function name or variable name into the target language.
- Keep the text short and concise, and avoid unnecessary details.
- Keep in mind that your audience is document readers, so use a deterministic tone to generate precise content and don't let them know you're provided with code snippet and documents.
- AVOID ANY SPECULATION and inaccurate descriptions!
- DO NOT use markdown syntax in the output

Now, provide the documentation for the target object in english in a professional way.
Please reason step by step, and always summarize your final answer using the following json format <output-format syntax="json">{{
    "description": "<docstring_description>",
    "exceptions": [
        {{"exception_class": "<module_exception_class_1>", "description": "<description_for_module_exception_1>"}}
        // ... more class attributes as needed
    ]
}}</output-format>. Stick to this format WITHOUT EXCEPTIONS and write valid json with quoted fields.

<think>
"""

    # TODO: add example back

    def build_check_outdated_prompt(self, code_object: GptInputCodeObject) -> str:
        existing_docstring = code_object.docstring

        prompt_length_without_context = len(
            self.check_outdated_prompt_template.format(
                code_type=code_object.code_type,
                code_name=code_object.name,
                code=code_object.code,
                existing_docstring=existing_docstring,
                context="",
            )
        )
        max_context_length = self.context_size - prompt_length_without_context

        context = self._build_context_from_code_object(code_object, max_context_length)
        self.logger.debug("Code Context length [%d/%d]", len(context), max_context_length)

        return self.check_outdated_prompt_template.format(
            code_type=code_object.code_type,
            code_name=code_object.name,
            code=code_object.code,
            existing_docstring=existing_docstring,
            context=context[:max_context_length],
        )

    def build_generate_docstring_prompt(self, code_object: GptInputCodeObject) -> str:
        if isinstance(code_object, GptInputMethodObject):
            prompt_template = self.generate_method_docstring_prompt_template
        elif isinstance(code_object, GptInputClassObject):
            prompt_template = self.generate_class_docstring_prompt_template
        elif isinstance(code_object, GptInputModuleObject):
            prompt_template = self.generate_module_docstring_prompt_template
        else:
            raise Exception("Unexpected code object type")

        prompt_length_without_context = len(
            prompt_template.format(code_name=code_object.name, code=code_object.code, context="")
        )
        max_context_length = self.context_size - prompt_length_without_context - 50  # buffer

        context = self._build_context_from_code_object(code_object, max_context_length)
        self.logger.debug("Code Context length [%d/%d]", len(context), max_context_length)

        return prompt_template.format(
            code=code_object.code, code_name=code_object.name, context=context[:max_context_length]
        )

    def _build_context_from_code_object(
        self, code_object: GptInputCodeObject, max_length: int
    ) -> str:
        if isinstance(code_object, GptInputMethodObject):
            context_summary = ""

            if code_object.context_objects is not None and code_object.context is not None:
                mapped_context: dict[str, list[ContextObject]] = {}
                for key, value in code_object.context.items():
                    if value is None:
                        continue
                    elif isinstance(value, int):
                        mapped_context[key] = [code_object.context_objects.get(value)]
                    elif isinstance(value, Iterable):
                        mapped_context[key] = [
                            code_object.context_objects.get(item) for item in value
                        ]
                    else:
                        raise Exception("Unexpected context type")

                raw_context_summary = ""
                for called_method in mapped_context["called_methods"]:
                    raw_context_summary += (
                        f"<called-method>\n{called_method.code}\n</called-method>\n"
                    )
                for called_class in mapped_context["called_classes"]:
                    raw_context_summary += f"<called-class>\n{called_class.code}\n</called-class>\n"
                for called_by_method in mapped_context["called_by_methods"]:
                    raw_context_summary += (
                        f"<called-by-method>\n{called_by_method.code}\n</called-by-method>\n"
                    )
                for called_by_class in mapped_context["called_by_classes"]:
                    raw_context_summary += (
                        f"<called-by-class>\n{called_by_class.code}\n</called-by-class>\n"
                    )
                for called_by_module in mapped_context["called_by_modules"]:
                    raw_context_summary += (
                        f"<called-by-module>\n{called_by_module.code}\n</called-by-module>\n"
                    )

            parent_context_summary = ""
            if (
                code_object.parent_method_id is not None
                and code_object.parent_method_id in code_object.context_objects
            ):
                parent_method = code_object.context_objects.get(code_object.parent_method_id)
                parent_context_summary += (
                    f"<parent-method>\n{parent_method.code}\n</parent-method>\n"
                )
            if (
                code_object.parent_class_id is not None
                and code_object.parent_class_id in code_object.context_objects
            ):
                parent_class = code_object.context_objects.get(code_object.parent_class_id)
                parent_context_summary += f"<parent-class>\n{parent_class.code}\n</parent-class>\n"
            if (
                code_object.parent_module_id is not None
                and code_object.parent_module_id in code_object.context_objects
                and code_object.context_objects.get(code_object.parent_module_id) is not None
            ):
                parent_module = code_object.context_objects.get(code_object.parent_module_id)
                parent_context_summary += (
                    f"<parent-module>\n{parent_module.code}\n</parent-module>\n"
                )

            raw_context_summary += parent_context_summary
            context_summary += f"<related-code>\n{raw_context_summary}</related-code>\n"

            full_context = f"""
{context_summary}
"""
            if len(full_context) <= max_length:
                return full_context

            medium_context = f"""
{parent_context_summary}
"""
            if len(medium_context) <= max_length:
                return medium_context

            no_context = ""
            if len(no_context) <= max_length:
                return no_context

            return code_object.code
        elif isinstance(code_object, GptInputClassObject):
            mapped_context: dict[str, list[ContextObject]] = {}
            for key, value in code_object.context.items():
                if value is None:
                    continue
                elif isinstance(value, int):
                    mapped_context[key] = [code_object.context_objects.get(value)]
                elif isinstance(value, Iterable):
                    mapped_context[key] = [code_object.context_objects.get(item) for item in value]
                else:
                    raise Exception("Unexpected context type")

            # context as code
            raw_context_summary = ""
            for called_method in mapped_context["called_methods"]:
                raw_context_summary += f"<called-method>\n{called_method.code}\n</called-method>\n"
            for called_class in mapped_context["called_classes"]:
                raw_context_summary += f"<called-class>\n{called_class.code}\n</called-class>\n"
            for called_by_method in mapped_context["called_by_methods"]:
                raw_context_summary += (
                    f"<called-by-method>\n{called_by_method.code}\n</called-by-method>\n"
                )
            for called_by_class in mapped_context["called_by_classes"]:
                raw_context_summary += (
                    f"<called-by-class>\n{called_by_class.code}\n</called-by-class>\n"
                )
            for called_by_module in mapped_context["called_by_modules"]:
                raw_context_summary += (
                    f"<called-by-module>\n{called_by_module.code}\n</called-by-module>\n"
                )
            for classes in mapped_context["class_ids"]:
                raw_context_summary += f"<sub-classes>\n{classes.code}\n</sub-classes>\n"
            for methods in mapped_context["method_ids"]:
                raw_context_summary += f"<class-methods>\n{methods.code}\n</class-methods>\n"

            # context as docstring if exists, else code
            raw_context_as_docstrings_or_code = ""
            for called_method in mapped_context["called_methods"]:
                if called_method.docstring is not None and len(called_method.docstring) > 10:
                    raw_context_as_docstrings_or_code += f"<called-method-docstring>\nMethod name:{called_method.name}\nDocstring:{called_method.docstring}\n</called-method-docstring>\n"
                else:
                    raw_context_as_docstrings_or_code += (
                        f"<called-method>\n{called_method.code}\n</called-method>\n"
                    )
            for called_class in mapped_context["called_classes"]:
                if called_class.docstring is not None and len(called_class.docstring) > 10:
                    raw_context_as_docstrings_or_code += f"<called-class-docstring>\nClass name:{called_class.name}\nDocstring:{called_class.docstring}\n</called-class-docstring>\n"
                else:
                    raw_context_as_docstrings_or_code += (
                        f"<called-class>\n{called_class.code}\n</called-class>\n"
                    )
            for called_by_method in mapped_context["called_by_methods"]:
                if called_by_method.docstring is not None and len(called_by_method.docstring) > 10:
                    raw_context_as_docstrings_or_code += f"<called-by-method-docstring>\nMethod name:{called_by_method.name}\nDocstring:{called_by_method.docstring}\n</called-by-method-docstring>\n"
                else:
                    raw_context_as_docstrings_or_code += (
                        f"<called-by-method>\n{called_by_method.code}\n</called-by-method>\n"
                    )
            for called_by_class in mapped_context["called_by_classes"]:
                if called_by_class.docstring is not None and len(called_by_class.docstring) > 10:
                    raw_context_as_docstrings_or_code += f"<called-by-class-docstring>\nClass name:{called_by_class.name}\nDocstring:{called_by_class.docstring}\n</called-by-class-docstring>\n"
                else:
                    raw_context_as_docstrings_or_code += (
                        f"<called-by-class>\n{called_by_class.code}\n</called-by-class>\n"
                    )
            for called_by_module in mapped_context["called_by_modules"]:
                if called_by_module.docstring is not None and len(called_by_module.docstring) > 10:
                    raw_context_as_docstrings_or_code += f"<called-by-module-docstring>\n{called_by_module.docstring}\n</called-by-module-docstring>\n"
                else:
                    raw_context_as_docstrings_or_code += (
                        f"<called-by-module>\n{called_by_module.code}\n</called-by-module>\n"
                    )
            for classes in mapped_context["class_ids"]:
                if classes.docstring is not None and len(classes.docstring) > 10:
                    raw_context_as_docstrings_or_code += f"<sub-classes-docstring>\nClass name:{classes.name}\nDocstring:{classes.docstring}\n</sub-classes-docstring>\n"
                else:
                    raw_context_as_docstrings_or_code += (
                        f"<sub-classes>\n{classes.code}\n</sub-classes>\n"
                    )
            for methods in mapped_context["method_ids"]:
                if methods.docstring is not None and len(methods.docstring) > 10:
                    raw_context_as_docstrings_or_code += f"<class-methods-docstring>\nMethod name:{methods.name}\nDocstring:{methods.docstring}\n</class-methods-docstring>\n"
                else:
                    raw_context_as_docstrings_or_code += (
                        f"<class-methods>\n{methods.code}\n</class-methods>\n"
                    )

            # context as docstrings
            raw_context_as_docstrings = ""
            for called_method in mapped_context["called_methods"]:
                raw_context_as_docstrings += f"<called-method-docstring>\nMethod name:{called_method.name}\nDocstring:{called_method.docstring}\n</called-method-docstring>\n"
            for called_class in mapped_context["called_classes"]:
                raw_context_as_docstrings += f"<called-class-docstring>\nClass name:{called_class.name}\nDocstring:{called_class.docstring}\n</called-class-docstring>\n"
            for called_by_method in mapped_context["called_by_methods"]:
                raw_context_as_docstrings += f"<called-by-method-docstring>\nMethod name:{called_by_method.name}\nDocstring:{called_by_method.docstring}\n</called-by-method-docstring>\n"
            for called_by_class in mapped_context["called_by_classes"]:
                raw_context_as_docstrings += f"<called-by-class-docstring>\nClass name:{called_by_class.name}\nDocstring:{called_by_class.docstring}\n</called-by-class-docstring>\n"
            for called_by_module in mapped_context["called_by_modules"]:
                raw_context_as_docstrings += f"<called-by-module-docstring>\n{called_by_module.docstring}\n</called-by-module-docstring>\n"
            for classes in mapped_context["class_ids"]:
                raw_context_as_docstrings += f"<sub-classes-docstring>\nClass name:{classes.name}\nDocstring:{classes.docstring}\n</sub-classes-docstring>\n"
            for methods in mapped_context["method_ids"]:
                raw_context_as_docstrings += f"<class-methods-docstring>\nMethod name:{methods.name}\nDocstring:{methods.docstring}\n</class-methods-docstring>\n"

            # context_summary += f"<related-code>\n{raw_context_summary}</related-code>\n"

            parent_context_summary = ""
            for parent in mapped_context["parent_id"]:
                parent_context_summary += f"<part-of-code>\n{parent.code}\n</part-of-code>\n"
            if code_object.context["parent_id"] != code_object.context["module_id"]:
                for module in mapped_context["module_id"]:
                    parent_context_summary += (
                        f"<part-of-module>\n{module.code}\n</part-of-module>\n"
                    )

            parent_context_as_docstrings = ""
            for parent in mapped_context["parent_id"]:
                parent_context_as_docstrings += f"<part-of-code>\nCode type: {parent.code_type}\nName: {parent.name}\nDocstring: {parent.docstring}\n</part-of-code>\n"
            if code_object.context["parent_id"] != code_object.context["module_id"]:
                for module in mapped_context["module_id"]:
                    parent_context_as_docstrings += (
                        f"<part-of-module>\n{module.docstring}\n</part-of-module>\n"
                    )

            # everything as code
            full_context = f"""<related-code>\n{raw_context_summary}{parent_context_summary}</related-code>\n"""
            if len(full_context) <= max_length:
                return full_context

            # context as code, parent as docstring
            full_context_parent_as_docstring = f"""<related-code>\n{raw_context_summary}{parent_context_as_docstrings}</related-code>\n"""
            if len(full_context_parent_as_docstring) <= max_length:
                return full_context_parent_as_docstring

            # context as code, parent omitted
            context_without_parent = f"""<related-code>\n{raw_context_summary}</related-code>\n"""
            if len(context_without_parent) <= max_length:
                return context_without_parent

            # context as docstring, if exists, else code, parent omitted
            context_as_docstring_or_code_without_parent = (
                f"""<related-code>\n{raw_context_as_docstrings_or_code}</related-code>\n"""
            )
            if len(context_as_docstring_or_code_without_parent) <= max_length:
                return context_as_docstring_or_code_without_parent

            # context as docstring, parent omitted
            context_without_parent_as_docstrings = (
                f"""<related-code>\n{raw_context_as_docstrings}</related-code>\n"""
            )
            if len(context_without_parent_as_docstrings) <= max_length:
                return context_without_parent_as_docstrings

            # no context
            no_context = ""
            if len(no_context) <= max_length:
                return no_context

            return ""
        elif isinstance(code_object, GptInputModuleObject):
            # TODO: build context from code object
            full_context = code_object.code

            return full_context
        else:
            raise Exception("Unexpected code object type")


class LocalDeepseekR1Strategy(DocstringModelStrategy):
    def __init__(self, device=None, context_size=2048):
        print("-------------------------", GPT4All.list_gpus(), "----------------------")
        super().__init__()
        if device is None:
            device = GPT4All.list_gpus()[0]

        # TODO: remove temp workaround
        # self.fallback_stategy = ModelStrategyFactory.create_strategy("mock")

        self.context_size = context_size

        self.prompt_builder = DeepseekR1PromptBuilder(context_size)

        self.model_name = "DeepSeek-R1-Distill-Llama-8B-Q4_0.gguf"

        self.logger.info(
            "Using GPT4All model [%s] with context size [%d]",
            self.model_name,
            self.context_size,
        )
        self.gpt_model = GPT4All(model_name=self.model_name, device=device)

        self.logger.info("Using device [%s], requested [%s]", self.gpt_model.device, device)

        if self.gpt_model.device is None:
            raise Exception("Unable to load gpt model")

    def check_outdated(self, code_object: GptInputCodeObject) -> bool:
        try:
            with self.gpt_model.chat_session():
                prompt = self.prompt_builder.build_check_outdated_prompt(code_object)

                save_data(
                    branch="class_docstrings",
                    code_type=code_object.code_type,
                    code_name=code_object.name,
                    code_id=code_object.id,
                    content_type="validation_prompt",
                    data=prompt,
                )  # update branch manually

                self.logger.debug("Using prompt [%s]", prompt)
                self.logger.info("Starting checking existing docstring")

                def generation_callback(token_id, token):
                    print(token, end="")

                    return True

                generated_text = self.gpt_model.generate(
                    prompt=prompt,
                    temp=0.6,
                    max_tokens=2000,
                    callback=generation_callback,
                )

                save_data(
                    branch="class_docstrings",
                    code_type=code_object.code_type,
                    code_name=code_object.name,
                    code_id=code_object.id,
                    content_type="validation_output",
                    data=generated_text,
                )  # update branch manually

                self.logger.info("Finished checking existing docstring [%s]", generated_text)

                docstring_matches = self._extract_check_outdated_output(generated_text)

                return not docstring_matches
        except Exception as e:
            self.logger.exception("An error occurred while checking existing docstring", exc_info=e)
            raise e

    def generate_docstring(self, code_object: GptInputCodeObject) -> GptOutput:
        if isinstance(code_object, gpt_input.GptInputMethodObject):
            try:
                with self.gpt_model.chat_session():
                    prompt = self.prompt_builder.build_generate_docstring_prompt(code_object)

                    self.logger.debug("Using prompt [%s]", prompt)
                    self.logger.info("Starting docstring generation")

                    def generation_callback(token_id, token):
                        print(token, end="")

                        return True

                    generated_text = self.gpt_model.generate(
                        prompt=prompt,
                        temp=0.6,
                        max_tokens=5000,
                        callback=generation_callback,
                    )

                    self.logger.info("Finished docstring generation [%s]", generated_text)

                    generated_output = self._extract_generate_docstring_json_output(generated_text)

                    # use generated_output to build gpt output object

                    try:
                        method_description = generated_output["description"]
                    except KeyError:
                        method_description = False

                    parameter_types: dict[str, str | bool] = {}
                    for parameter_name in code_object.parameters:
                        try:
                            generated_parameters = generated_output["parameters"]
                            matching_parameter = next(
                                filter(
                                    lambda x: "name" in x and x["name"] == parameter_name,
                                    generated_parameters,
                                )
                            )

                            parameter_types[parameter_name] = matching_parameter["type"]
                        except StopIteration:
                            parameter_types[parameter_name] = False
                        except KeyError:
                            parameter_types[parameter_name] = False
                        except Exception as e:
                            self.logger.exception(
                                f"An unkown error occurred while extracting generated type for parameter [{parameter_name}]",
                                exc_info=e,
                            )
                            parameter_types[parameter_name] = False

                    parameter_descriptions: dict[str, str | bool] = {}
                    for parameter_name in code_object.parameters:
                        try:
                            generated_parameters = generated_output[parameter_name] = (
                                generated_output["parameters"]
                            )
                            matching_parameter = next(
                                filter(
                                    lambda x: "name" in x and x["name"] == parameter_name,
                                    generated_parameters,
                                )
                            )
                            parameter_descriptions[parameter_name] = matching_parameter[
                                "description"
                            ]
                        except StopIteration:
                            parameter_descriptions[parameter_name] = False
                        except KeyError:
                            parameter_descriptions[parameter_name] = False
                        except Exception as e:
                            self.logger.warning(
                                f"An unkown error occurred while extracting generated description for parameter [{parameter_name}]",
                                exc_info=e,
                            )
                            parameter_descriptions[parameter_name] = False

                    exception_descriptions: dict[str, str | bool] = {}
                    for exception in code_object.exceptions:
                        try:
                            generated_parameters = generated_output[exception] = generated_output[
                                "parameters"
                            ]
                            matching_exception = next(
                                filter(
                                    lambda x: "name" in x and x["name"] == parameter_name,
                                    generated_parameters,
                                )
                            )
                            parameter_descriptions[parameter_name] = matching_exception[
                                "description"
                            ]
                        except StopIteration:
                            parameter_descriptions[parameter_name] = False
                        except KeyError:
                            parameter_descriptions[parameter_name] = False
                        except Exception as e:
                            self.logger.warning(
                                f"An unkown error occurred while extracting generated description for parameter [{parameter_name}]",
                                exc_info=e,
                            )
                            parameter_descriptions[parameter_name] = False

                    return_type: str | bool = False
                    if code_object.return_missing:
                        try:
                            return_type = generated_output["returns"]["type"]
                        except KeyError:
                            pass

                    try:
                        return_description = generated_output["returns"]["description"]
                    except KeyError:
                        return_description = False

                    return GptOutputMethod(
                        id=code_object.id,
                        no_change_necessary=False,
                        description=method_description,
                        parameter_types=parameter_types,
                        parameter_descriptions=parameter_descriptions,
                        return_description=return_description,
                        return_type=return_type,
                        exception_descriptions=exception_descriptions,
                    )
            except KeyboardInterrupt as e:
                # Let user abort execution
                raise e
            except Exception as e:
                self.logger.exception(
                    "An unkown error occurred during docstring generation, switching to fallback strategy",
                    exc_info=e,
                )

                # TODO: Error handling not implement yet
                return self.fallback_stategy.generate_docstring(code_object)
        elif isinstance(code_object, gpt_input.GptInputClassObject):
            try:
                with self.gpt_model.chat_session():
                    prompt = self.prompt_builder.build_generate_docstring_prompt(code_object)

                    save_data(
                        branch="class_docstrings",
                        code_type=code_object.code_type,
                        code_name=code_object.name,
                        code_id=code_object.id,
                        content_type="generation_prompt",
                        data=prompt,
                    )  # update branch manually here

                    self.logger.debug("Using prompt [%s]", prompt)
                    self.logger.info("Starting docstring generation")

                    def generation_callback(token_id, token):
                        print(token, end="")

                        return True

                    generated_text = self.gpt_model.generate(
                        prompt=prompt,
                        temp=0.6,
                        max_tokens=5000,
                        callback=generation_callback,
                    )

                    self.logger.info("Finished docstring generation [%s]", generated_text)

                    generated_output = self._extract_generate_docstring_json_output(generated_text)

                    save_data(
                        branch="class_docstrings",
                        code_type=code_object.code_type,
                        code_name=code_object.name,
                        code_id=code_object.id,
                        content_type="generation_output",
                        data=generated_output,
                    )  # update branch manually here

                    # use generated_output to build gpt output object

                    try:
                        class_description = generated_output["description"]
                    except KeyError:
                        class_description = False

                    # extract class attributes
                    class_attribute_descriptions: dict[str, str | bool] = {}
                    class_attribute_types: dict[str, str | bool] = {}

                    for class_attribute in code_object.class_attributes:
                        class_attribute_name = class_attribute["name"]
                        try:
                            generated_class_attributes = generated_output["class_attributes"]
                            matching_class_attribute = next(
                                filter(
                                    lambda x: "name" in x and x["name"] == class_attribute_name,
                                    generated_class_attributes,
                                )
                            )
                            class_attribute_descriptions[class_attribute_name] = (
                                matching_class_attribute["description"]
                            )
                            class_attribute_types[class_attribute_name] = matching_class_attribute[
                                "type"
                            ]
                        except StopIteration:
                            class_attribute_descriptions[class_attribute_name] = False
                            class_attribute_types[class_attribute_name] = False
                        except KeyError:
                            class_attribute_descriptions[class_attribute_name] = False
                            class_attribute_types[class_attribute_name] = False
                        except Exception as e:
                            self.logger.warning(
                                f"An unkown error occurred while extracting generated description for class attribute [{class_attribute_name}]",
                                exc_info=e,
                            )
                            class_attribute_descriptions[class_attribute_name] = False
                            class_attribute_types[class_attribute_name] = False

                    # extract instance attributes
                    instance_attribute_descriptions: dict[str, str | bool] = {}
                    instance_attribute_types: dict[str, str | bool] = {}

                    for instance_attribute_name in code_object.instance_attributes:
                        try:
                            generated_instance_attributes = generated_output["instance_attributes"]
                            matching_instance_attribute = next(
                                filter(
                                    lambda x: "name" in x and x["name"] == instance_attribute_name,
                                    generated_instance_attributes,
                                )
                            )

                            instance_attribute_descriptions[instance_attribute_name] = (
                                matching_instance_attribute["description"]
                            )
                            instance_attribute_types[instance_attribute_name] = (
                                matching_instance_attribute["type"]
                            )
                        except StopIteration:
                            instance_attribute_descriptions[instance_attribute_name] = False
                            instance_attribute_types[instance_attribute_name] = False
                        except KeyError:
                            instance_attribute_descriptions[instance_attribute_name] = False
                            instance_attribute_types[instance_attribute_name] = False
                        except Exception as e:
                            self.logger.exception(
                                f"An unkown error occurred while extracting generated type for class attribute [{instance_attribute_name}]",
                                exc_info=e,
                            )
                            instance_attribute_descriptions[instance_attribute_name] = False
                            instance_attribute_types[instance_attribute_name] = False

                    return GptOutputClass(
                        id=code_object.id,
                        no_change_necessary=False,
                        description=class_description,
                        class_attribute_descriptions=class_attribute_descriptions,
                        class_attribute_types=class_attribute_types,
                        instance_attribute_descriptions=instance_attribute_descriptions,
                        instance_attribute_types=instance_attribute_types,
                    )
            except KeyboardInterrupt as e:
                # Let user abort execution
                raise e
            except Exception as e:
                self.logger.exception(
                    "An unkown error occurred during docstring generation, switching to fallback strategy",
                    exc_info=e,
                )

                # TODO: Error handling not implement yet
                return self.fallback_stategy.generate_docstring(code_object)
        elif isinstance(code_object, gpt_input.GptInputModuleObject):
            try:
                with self.gpt_model.chat_session():
                    prompt = self.prompt_builder.build_generate_docstring_prompt(code_object)

                    self.logger.debug("Using prompt [%s]", prompt)
                    self.logger.info("Starting docstring generation")

                    def generation_callback(token_id, token):
                        print(token, end="")

                        return True

                    generated_text = self.gpt_model.generate(
                        prompt=prompt,
                        temp=0.6,
                        max_tokens=5000,
                        callback=generation_callback,
                    )

                    self.logger.info("Finished docstring generation [%s]", generated_text)

                    generated_output = self._extract_generate_docstring_json_output(generated_text)

                    # use generated_output to build gpt output object

                    try:
                        module_description = generated_output["description"]
                    except KeyError:
                        module_description = False

                    # extract module exceptions
                    exception_descriptions: dict[str, str | bool] = {}

                    for exception_class in code_object.exceptions:
                        try:
                            generated_exceptions = generated_output["exceptions"]
                            matching_exception = next(
                                filter(
                                    lambda x: "exception_class" in x
                                    and x["exception_class"] == exception_class,
                                    generated_exceptions,
                                )
                            )

                            exception_descriptions[exception_class] = matching_exception[
                                "description"
                            ]
                        except StopIteration:
                            exception_descriptions[exception_class] = False
                        except KeyError:
                            exception_descriptions[exception_class] = False
                        except Exception as e:
                            self.logger.exception(
                                f"An unkown error occurred while extracting generated description for module exception [{exception_class}]",
                                exc_info=e,
                            )
                            exception_descriptions[exception_class] = False

                    return GptOutputModule(
                        id=code_object.id,
                        no_change_necessary=False,
                        description=module_description,
                        exception_descriptions=exception_descriptions,
                    )
            except KeyboardInterrupt as e:
                # Let user abort execution
                raise e
            except Exception as e:
                self.logger.exception(
                    "An unkown error occurred during docstring generation, switching to fallback strategy",
                    exc_info=e,
                )

                # TODO: Error handling not implement yet
                return self.fallback_stategy.generate_docstring(code_object)
        else:
            # Not Implement Yet
            return self.fallback_stategy.generate_docstring(code_object)

    def _extract_check_outdated_output(self, result: str) -> bool:
        match = re.search(CHECK_OUTDATED_JSON_OUTPUT_REGEX, result, re.DOTALL | re.IGNORECASE)

        if match is None or match.group(1) is None:
            raise ValueError("No JSON match found")

        analysis_json_str = match.group(1)
        analysis_json = json5.loads(analysis_json_str)

        return "matches" in analysis_json and analysis_json["matches"]

    def _extract_generate_docstring_json_output(self, result: str) -> dict:
        match = re.search(DOCSTRING_GENERATION_JSON_OUTPUT_REGEX, result, re.DOTALL | re.IGNORECASE)

        if match is None:
            raise ValueError("No JSON match found")

        analysis_json_str = match.group(0)
        analysis_json = json5.loads(analysis_json_str)

        return analysis_json
