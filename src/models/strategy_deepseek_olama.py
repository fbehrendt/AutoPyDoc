import logging
import re
from base64 import b64encode
from collections.abc import Iterable
from typing import Optional
from urllib.parse import urlparse, urlunparse

import json5
from ollama import Client

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
You are an AI documentation assistant, and your task is to evaluate if an existing docstring for {code_type} {code_name} correctly describes the given code of the {code_type}.
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
You are an AI documentation assistant, and your task is to analyze the code of a Python class called {code_name}.
The purpose of the analysis is to help developers and beginners understand the class and specific usage of the code.
Use plain text (including all details), in a deterministic tone.

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
You are an AI documentation assistant, and your task is to analyze the code of a Python module called {code_name}.
The purpose of the analysis is to help developers and beginners understand the module and specific usage of the code.
Use plain text (including all details), in a deterministic tone.

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
            prompt_template.format(context="", code_name=code_object.name)
        )
        max_context_length = self.context_size - prompt_length_without_context

        context = self._build_context_from_code_object(code_object, max_context_length)
        self.logger.debug("Code Context length [%d/%d]", len(context), max_context_length)

        return prompt_template.format(
            context=context[:max_context_length], code_name=code_object.name
        )

    # Helper to map context ids to objects
    def _map_context(self, code_object: GptInputCodeObject) -> dict[str, list[any]]:
        mapped_context: dict[str, list[any]] = {}

        if code_object.context_objects is None or code_object.context is None:
            return mapped_context

        for key, value in code_object.context.items():
            items = []

            if value is None:
                continue

            elif isinstance(value, int):
                obj = code_object.context_objects.get(value)
                if obj:
                    items.append(obj)
            elif isinstance(value, Iterable):
                for item_id in value:
                    obj = code_object.context_objects.get(item_id)
                    if obj:
                        items.append(obj)
            else:
                logging.warning(f"Unexpected context type for key [{key}]=[{type(value)}]")
                continue  # Skip this key

            mapped_context[key] = items
        return mapped_context

    # Helper function to get context object and its docstring
    def _get_docstring_context(
        self, obj_id: Optional[int], context_objects: Optional[dict[int, any]], tag: str
    ) -> str:
        if obj_id is None or context_objects is None or obj_id not in context_objects:
            return ""

        obj = context_objects.get(obj_id)

        if obj is not None and obj.docstring:
            return f"<{tag}>\n{obj.docstring}\n</{tag}>\n"

        return ""

    def _build_context_from_code_object(
        self, code_object: GptInputCodeObject, max_length: int
    ) -> str:
        if isinstance(code_object, GptInputMethodObject):
            context_summary = ""

            if code_object.context_objects is not None and code_object.context is not None:
                mapped_context = self._map_context(code_object)

                raw_context_summary = ""
                for called_method in mapped_context["called_methods"]:
                    raw_context_summary += (
                        f"<called-method>\n{called_method.docstring}\n</called-method>\n"
                    )
                for called_class in mapped_context["called_classes"]:
                    raw_context_summary += (
                        f"<called-class>\n{called_class.docstring}\n</called-class>\n"
                    )
                for called_by_method in mapped_context["called_by_methods"]:
                    raw_context_summary += (
                        f"<called-by-method>\n{called_by_method.docstring}\n</called-by-method>\n"
                    )
                for called_by_class in mapped_context["called_by_classes"]:
                    raw_context_summary += (
                        f"<called-by-class>\n{called_by_class.docstring}\n</called-by-class>\n"
                    )
                for called_by_module in mapped_context["called_by_modules"]:
                    raw_context_summary += (
                        f"<called-by-module>\n{called_by_module.docstring}\n</called-by-module>\n"
                    )

                context_summary += raw_context_summary

            parent_context_summary = (
                self._get_docstring_context(
                    code_object.parent_method_id, code_object.context_objects, "parent-method"
                )
                + self._get_docstring_context(
                    code_object.parent_class_id, code_object.context_objects, "parent-class"
                )
                + self._get_docstring_context(
                    code_object.parent_module_id, code_object.context_objects, "parent-module"
                )
            )

            method_summary = f"""
The method to generate the docstring for:
<method name="{code_object.name}">
{code_object.code}
</method>
"""

            biggest_context = f"""
{method_summary}

The context of the method is as follows:
<related-code>
{context_summary}
{parent_context_summary}
</related-code>
"""
            if len(biggest_context) <= max_length:
                return biggest_context

            medium_context = f"""
{method_summary}

The context of the method is as follows:
<related-code>
{parent_context_summary}
</related-code>
"""
            if len(medium_context) <= max_length:
                return medium_context

            small_context = method_summary
            if len(small_context) <= max_length:
                return small_context

            if len(code_object.code) <= max_length:
                return code_object.code
            else:
                return code_object.code[: max_length - 3] + "..."
        elif isinstance(code_object, GptInputClassObject):
            context_summary = ""

            if code_object.context_objects is not None and code_object.context is not None:
                mapped_context = self._map_context(code_object)

                raw_context_summary = ""

                for called_by_method in mapped_context.get("called_by_methods", []):
                    if called_by_method.docstring:
                        raw_context_summary += f'<called-by-method name="{called_by_method.name}">\n{called_by_method.docstring}\n</called-by-method>\n'
                for called_by_class in mapped_context.get("called_by_classes", []):
                    if called_by_class.docstring:
                        raw_context_summary += f'<called-by-class name="{called_by_class.name}">\n{called_by_class.docstring}\n</called-by-class>\n'
                for called_by_module in mapped_context.get("called_by_modules", []):
                    if called_by_module.docstring:
                        raw_context_summary += f'<called-by-module name="{called_by_module.name}">\n{called_by_module.docstring}\n</called-by-module>\n'

                context_summary += raw_context_summary

            parent_inheritance_summary = ""
            parent_inheritance_summary += self._get_docstring_context(
                code_object.parent_method_id, code_object.context_objects, "parent-method"
            )
            parent_inheritance_summary += self._get_docstring_context(
                code_object.parent_class_id, code_object.context_objects, "parent-class"
            )
            parent_inheritance_summary += self._get_docstring_context(
                code_object.parent_module_id, code_object.context_objects, "parent-module"
            )
            parent_inheritance_summary += self._get_docstring_context(
                code_object.inherited_from, code_object.context_objects, "base-class"
            )

            child_context_summary = ""
            if code_object.context_objects:
                for method_id in code_object.method_ids:
                    child_context_summary += self._get_docstring_context(
                        method_id, code_object.context_objects, "child-method"
                    )
                for class_id in code_object.class_ids:
                    child_context_summary += self._get_docstring_context(
                        class_id, code_object.context_objects, "child-class"
                    )

            class_summary = f"""
The class to generate the docstring for:
<class name="{code_object.name}">
{code_object.code}
</class>
"""
            biggest_context = f"""
{class_summary}

The context of the class is as follows:
<related-code>
{context_summary}
{parent_inheritance_summary}
{child_context_summary}
</related-code>
"""
            if len(biggest_context) <= max_length:
                return biggest_context

            medium_context = f"""
{class_summary}

The context of the class is as follows:
<related-code>
{parent_inheritance_summary}
{child_context_summary}
</related-code>
"""
            if len(medium_context) <= max_length:
                return medium_context

            small_context = class_summary
            if len(small_context) <= max_length:
                return small_context

            if len(code_object.code) <= max_length:
                return code_object.code
            else:
                return code_object.code[: max_length - 3] + "..."

        elif isinstance(code_object, GptInputModuleObject):
            child_context_summary = ""
            if code_object.context_objects:
                for func_id in code_object.method_ids:
                    child_context_summary += self._get_docstring_context(
                        func_id, code_object.context_objects, "child-function"
                    )
                for class_id in code_object.class_ids:
                    child_context_summary += self._get_docstring_context(
                        class_id, code_object.context_objects, "child-class"
                    )

            module_summary = f"""
The module to generate the docstring for:
<module name="{code_object.name}">
{code_object.code}
</module>
"""

            biggest_context = f"""
{module_summary}

The context of the module is as follows:
<related-code>
{child_context_summary}
</related-code>
"""
            if len(biggest_context) <= max_length:
                return biggest_context

            small_context = module_summary
            if len(small_context) <= max_length:
                return small_context

            if len(code_object.code) <= max_length:
                return code_object.code
            else:
                return code_object.code[: max_length - 3] + "..."
        else:
            raise Exception("Unexpected code object type")


class OllamaDeepseekR1Strategy(DocstringModelStrategy):
    def __init__(self, context_size=2048, ollama_host=None):
        super().__init__()

        # TODO: remove temp workaround
        # self.fallback_stategy = ModelStrategyFactory.create_strategy("mock")

        self.context_size = context_size

        self.prompt_builder = DeepseekR1PromptBuilder(context_size)

        self.model_name = "deepseek-r1:8b"

        self.logger.info(
            "Using GPT4All model [%s] with context size [%d]",
            self.model_name,
            self.context_size,
        )

        (url, headers) = extract_authentication(ollama_host)

        self.client = Client(
            host=url,
            headers=headers,
        )

    def check_outdated(self, code_object: GptInputCodeObject) -> bool:
        try:
            prompt = self.prompt_builder.build_check_outdated_prompt(code_object)

            self.logger.debug("Using prompt [%s]", prompt)
            self.logger.info("Starting checking existing docstring")

            stream = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                format={
                    "type": "object",
                    "properties": {
                        "analysis": {"type": "string"},
                        "matches": {"type": "boolean"},
                    },
                    "required": ["analysis", "matches"],
                },
                stream=True,
                options={"num_ctx": self.context_size, "temperature": 0.6},
            )

            generated_text = ""

            for chunk in stream:
                print(chunk["response"], end="", flush=True)
                generated_text += chunk["response"]

            self.logger.info("Finished checking existing docstring [%s]", generated_text)

            docstring_matches = self._extract_check_outdated_output(generated_text)

            return not docstring_matches
        except Exception as e:
            self.logger.exception("An error occurred while checking existing docstring", exc_info=e)
            raise e

    def generate_docstring(self, code_object: GptInputCodeObject) -> GptOutput:
        if isinstance(code_object, gpt_input.GptInputMethodObject):
            try:
                prompt = self.prompt_builder.build_generate_docstring_prompt(code_object)

                self.logger.debug("Using prompt [%s]", prompt)
                self.logger.info("Starting docstring generation")

                stream = self.client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    # format={
                    #     "type": "object",
                    #     "properties": {
                    #         "description": {"type": "string"},
                    #         "parameters": {
                    #             "type": "array",
                    #             "items": {
                    #                 "type": "object",
                    #                 "properties": {
                    #                     "name": {
                    #                         "type": "string",
                    #                     },
                    #                     "type": {
                    #                         "type": "string",
                    #                     },
                    #                     "description": {
                    #                         "type": "string",
                    #                     },
                    #                 },
                    #                 "required": ["name", "type", "description"],
                    #             },
                    #         },
                    #         "returns": {
                    #             "type": "object",
                    #             "properties": {
                    #                 "type": {
                    #                     "type": "string",
                    #                 },
                    #                 "description": {
                    #                     "type": "string",
                    #                 },
                    #             },
                    #             "required": ["type", "description"],
                    #         },
                    #     },
                    #     "required": ["description", "parameters", "returns"],
                    # },
                    stream=True,
                    options={"num_ctx": self.context_size, "temperature": 0.6},
                )

                generated_text = ""

                for chunk in stream:
                    print(chunk["response"], end="", flush=True)
                    generated_text += chunk["response"]

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
                        matching_instance_attribute = next(
                            filter(
                                lambda x: "name" in x and x["name"] == parameter_name,
                                generated_parameters,
                            )
                        )

                        parameter_types[parameter_name] = matching_instance_attribute["type"]
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
                        generated_parameters = generated_output[parameter_name] = generated_output[
                            "parameters"
                        ]
                        matching_instance_attribute = next(
                            filter(
                                lambda x: "name" in x and x["name"] == parameter_name,
                                generated_parameters,
                            )
                        )
                        parameter_descriptions[parameter_name] = matching_instance_attribute[
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
                        matching_instance_attribute = next(
                            filter(
                                lambda x: "name" in x and x["name"] == parameter_name,
                                generated_parameters,
                            )
                        )
                        parameter_descriptions[parameter_name] = matching_instance_attribute[
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
                # return self.fallback_stategy.generate_docstring(code_object)
                raise e
        elif isinstance(code_object, gpt_input.GptInputClassObject):
            try:
                prompt = self.prompt_builder.build_generate_docstring_prompt(code_object)

                self.logger.debug("Using prompt [%s]", prompt)
                self.logger.info("Starting docstring generation")

                stream = self.client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    # format={
                    #     "type": "object",
                    #     "properties": {
                    #         "description": {"type": "string"},
                    #         "class_attributes": {
                    #             "type": "array",
                    #             "items": {
                    #                 "type": "object",
                    #                 "properties": {
                    #                     "name": {
                    #                         "type": "string",
                    #                     },
                    #                     "type": {
                    #                         "type": "string",
                    #                     },
                    #                     "description": {
                    #                         "type": "string",
                    #                     },
                    #                 },
                    #                 "required": ["name", "type", "description"],
                    #             },
                    #         },
                    #         "instance_attributes": {
                    #             "type": "array",
                    #             "items": {
                    #                 "type": "object",
                    #                 "properties": {
                    #                     "name": {
                    #                         "type": "string",
                    #                     },
                    #                     "type": {
                    #                         "type": "string",
                    #                     },
                    #                     "description": {
                    #                         "type": "string",
                    #                     },
                    #                 },
                    #                 "required": ["name", "type", "description"],
                    #             },
                    #         },
                    #     },
                    #     "required": ["description", "class_attributes", "instance_attributes"],
                    # },
                    stream=True,
                    options={"num_ctx": self.context_size, "temperature": 0.6},
                )

                generated_text = ""

                for chunk in stream:
                    print(chunk["response"], end="", flush=True)
                    generated_text += chunk["response"]

                self.logger.info("Finished docstring generation [%s]", generated_text)

                generated_output = self._extract_generate_docstring_json_output(generated_text)

                # use generated_output to build gpt output object

                try:
                    class_description = generated_output["description"]
                except KeyError:
                    class_description = False

                # extract class attributes
                class_attribute_descriptions: dict[str, str | bool] = {}
                class_attribute_types: dict[str, str | bool] = {}

                for instance_attribute_name in code_object.class_attributes:
                    try:
                        generated_exceptions = generated_output[instance_attribute_name] = (
                            generated_output["class_attributes"]
                        )
                        matching_instance_attribute = next(
                            filter(
                                lambda x: "name" in x and x["name"] == instance_attribute_name,
                                generated_exceptions,
                            )
                        )
                        class_attribute_descriptions[instance_attribute_name] = (
                            matching_instance_attribute["description"]
                        )
                        class_attribute_types[instance_attribute_name] = (
                            matching_instance_attribute["type"]
                        )
                    except StopIteration:
                        class_attribute_descriptions[instance_attribute_name] = False
                        class_attribute_types[instance_attribute_name] = False
                    except KeyError:
                        class_attribute_descriptions[instance_attribute_name] = False
                        class_attribute_types[instance_attribute_name] = False
                    except Exception as e:
                        self.logger.warning(
                            f"An unkown error occurred while extracting generated description for class attribute [{instance_attribute_name}]",
                            exc_info=e,
                        )
                        class_attribute_descriptions[instance_attribute_name] = False
                        class_attribute_types[instance_attribute_name] = False

                # extract instance attributes
                instance_attribute_descriptions: dict[str, str | bool] = {}
                instance_attribute_types: dict[str, str | bool] = {}

                for instance_attribute in code_object.instance_attributes:
                    instance_attribute_name = instance_attribute["name"]

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
                # return self.fallback_stategy.generate_docstring(code_object)
                raise e
        elif isinstance(code_object, gpt_input.GptInputModuleObject):
            try:
                prompt = self.prompt_builder.build_generate_docstring_prompt(code_object)

                self.logger.debug("Using prompt [%s]", prompt)
                self.logger.info("Starting docstring generation")

                stream = self.client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    # format={
                    #     "type": "object",
                    #     "properties": {
                    #         "description": {"type": "string"},
                    #         "exceptions": {
                    #             "type": "array",
                    #             "items": {
                    #                 "type": "object",
                    #                 "properties": {
                    #                     "exception_class": {
                    #                         "type": "string",
                    #                     },
                    #                     "description": {
                    #                         "type": "string",
                    #                     },
                    #                 },
                    #                 "required": ["exception_class", "description"],
                    #             },
                    #         },
                    #     },
                    #     "required": ["description", "parameters"],
                    # },
                    stream=True,
                    options={"num_ctx": self.context_size, "temperature": 0.6},
                )

                generated_text = ""

                for chunk in stream:
                    generated_text += chunk["response"]

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
                        matching_instance_attribute = next(
                            filter(
                                lambda x: "exception_class" in x
                                and x["exception_class"] == exception_class,
                                generated_exceptions,
                            )
                        )

                        exception_descriptions[exception_class] = matching_instance_attribute[
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
                # return self.fallback_stategy.generate_docstring(code_object)
                raise e
        else:
            raise Exception("Unexpected code object type")

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


def extract_authentication(url: str) -> tuple[str, dict[str, str]]:
    parsed_url = urlparse(url)
    headers = {}
    stripped_url_str = url

    if parsed_url.username:
        username = parsed_url.username
        password = parsed_url.password or ""

        auth_string = f"{username}:{password}"

        encoded_bytes = b64encode(auth_string.encode("utf-8"))
        headers = {"Authorization": f"Basic {encoded_bytes.decode('ascii')}"}

        new_netloc = parsed_url.hostname
        if parsed_url.port:
            new_netloc += f":{parsed_url.port}"

        stripped_url_parts = parsed_url._replace(netloc=new_netloc)
        stripped_url_str = urlunparse(stripped_url_parts)

    return stripped_url_str, headers
