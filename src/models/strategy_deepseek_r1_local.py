import logging
import re
from collections.abc import Iterable

import json5
from gpt4all import GPT4All

import gpt_input
from gpt_input import (
    GptInputClassObject,
    GptInputCodeObject,
    GptInputMethodObject,
    GptInputModuleObject,
    GptOutput,
    GptOutputMethod,
)

from .model_factory import ModelStrategyFactory
from .model_strategy import DocstringModelStrategy

CHECK_OUTDATED_JSON_OUTPUT_REGEX = (
    r'({\s*"analysis":\s*"(.*)"\s*,\s*"matches"\s*:\s*(true|false)\s*})'
)
DOCSTRING_GENERATION_JSON_OUTPUT_REGEX = r"{.*}"


class DeepseekR1PromptBuilder:
    def __init__(self, context_size: int):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.context_size = context_size

        self.check_outdated_prompt_template = """
You are an AI documentation assistant, and your task is to evaluate if an existing function docstring correctly describes the given code of the function.
The purpose of the documentation is to help developers and beginners understand the function and specific usage of the code.
If any part of the docstring is inadequate, consider the whole docstring to be inadequate. Any mocked docstring is to be considered inadequate.

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
You are an AI documentation assistant, and your task is to analyze the code of a Python function.
The purpose of the analysis is to help developers and beginners understand the function and specific usage of the code.
Use plain text (including all details), in a deterministic tone.

The content of the function is as follows:
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

    def build_check_outdated_prompt(self, code_object: GptInputCodeObject) -> str:
        existing_docstring = code_object.docstring

        prompt_length_without_context = len(
            self.check_outdated_prompt_template.format(
                existing_docstring=existing_docstring,
                context="",
            )
        )
        max_context_length = self.context_size - prompt_length_without_context

        context = self._build_context_from_code_object(code_object, max_context_length)
        self.logger.debug("Code Context length [%d/%d]", len(context), max_context_length)

        return self.check_outdated_prompt_template.format(
            existing_docstring=existing_docstring,
            context=context[:max_context_length],
        )

    def build_generate_method_docstring_prompt(self, code_object: GptInputCodeObject) -> str:
        prompt_length_without_context = len(
            self.generate_method_docstring_prompt_template.format(context="")
        )
        max_context_length = self.context_size - prompt_length_without_context

        context = self._build_context_from_code_object(code_object, max_context_length)
        self.logger.debug("Code Context length [%d/%d]", len(context), max_context_length)

        return self.generate_method_docstring_prompt_template.format(
            context=context[:max_context_length]
        )

    def _build_context_from_code_object(
        self, code_object: GptInputCodeObject, max_length: int
    ) -> str:
        if isinstance(code_object, GptInputMethodObject):
            context_summary = ""

            if code_object.context_docstrings is not None and code_object.context is not None:
                mapped_context: dict[str, list[str]] = {}
                for key, value in code_object.context.items():
                    if value is None:
                        continue
                    elif isinstance(value, int):
                        mapped_context[key] = [code_object.context_docstrings.get(value)]
                    elif isinstance(value, Iterable):
                        mapped_context[key] = [
                            code_object.context_docstrings.get(item) for item in value
                        ]
                    else:
                        raise Exception("Unexpected context type")

                raw_context_summary = ""
                for called_method in mapped_context["called_methods"]:
                    raw_context_summary += f"<called-method>\n{called_method}\n</called-method>\n"
                for called_class in mapped_context["called_classes"]:
                    raw_context_summary += f"<called-class>\n{called_class}\n</called-class>\n"
                for called_by_method in mapped_context["called_by_methods"]:
                    raw_context_summary += (
                        f"<called-by-method>\n{called_by_method}\n</called-by-method>\n"
                    )
                for called_by_class in mapped_context["called_by_classes"]:
                    raw_context_summary += (
                        f"<called-by-class>\n{called_by_class}\n</called-by-class>\n"
                    )
                for called_by_module in mapped_context["called_by_modules"]:
                    raw_context_summary += (
                        f"<called-by-module>\n{called_by_module}\n</called-by-module>\n"
                    )

                context_summary += f"<related-code>\n{raw_context_summary}</related-code>\n"

            parent_context_summary = ""
            if (
                code_object.parent_method_id is not None
                and code_object.parent_method_id in code_object.context_docstrings
            ):
                parent_context_summary += f"<parent-method>\n{code_object.context_docstrings.get(code_object.parent_method_id)}\n</parent-method>\n"
            if (
                code_object.parent_class_id is not None
                and code_object.parent_class_id in code_object.context_docstrings
            ):
                parent_context_summary += f"<parent-class>\n{code_object.context_docstrings.get(code_object.parent_class_id)}\n</parent-class>\n"
            if (
                code_object.parent_module_id is not None
                and code_object.parent_module_id in code_object.context_docstrings
                and code_object.context_docstrings.get(code_object.parent_module_id) is not None
            ):
                parent_context_summary += f"<parent-module>\n{code_object.context_docstrings.get(code_object.parent_module_id)}\n</parent-module>\n"

            method_summary = f"""
<method name="{code_object.name}">
{code_object.code}
</method>
"""

            biggest_context = f"""
{context_summary}
{parent_context_summary}
{method_summary}
"""
            if len(biggest_context) <= max_length:
                return biggest_context

            medium_context = f"""
{parent_context_summary}
{method_summary}
"""
            if len(medium_context) <= max_length:
                return medium_context

            small_context = method_summary
            if len(small_context) <= max_length:
                return small_context

            return code_object.code
        elif isinstance(code_object, GptInputClassObject):
            biggest_context = code_object.code
        elif isinstance(code_object, GptInputModuleObject):
            biggest_context = code_object.code
        else:
            raise Exception("Unexpected code object type")


class LocalDeepseekR1Strategy(DocstringModelStrategy):
    def __init__(self, device="cuda", context_size=2048):
        super().__init__()

        # TODO: remove temp workaround
        self.fallback_stategy = ModelStrategyFactory.create_strategy("mock")

        self.device = device
        self.context_size = context_size

        self.prompt_builder = DeepseekR1PromptBuilder(context_size)

        model_name = "DeepSeek-R1-Distill-Llama-8B-Q4_0.gguf"

        self.logger.info(
            "Using GPT4All model [%s] with context size [%d]",
            model_name,
            self.context_size,
        )
        self.gpt_model = GPT4All(model_name=model_name, device=self.device)

        self.logger.info("Using device [%s], requested [%s]", self.gpt_model.device, self.device)

        if self.gpt_model.device is None:
            raise Exception("Unable to load gpt model")

    def check_outdated(self, code_object: GptInputCodeObject) -> bool:
        return True

        try:
            with self.gpt_model.chat_session():
                prompt = self.prompt_builder.build_check_outdated_prompt(code_object)

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
                    prompt = self.prompt_builder.build_generate_method_docstring_prompt(code_object)

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

                    generated_output = self._extract_generate_docstring_output(generated_text)

                    # use generated_output to build gpt output object

                    try:
                        method_description = generated_output["description"]
                    except KeyError:
                        method_description = False

                    param_types: dict[str, str | bool] = {}
                    for param_name in code_object.parameters:
                        try:
                            generated_parameters = generated_output["parameters"]
                            matching_param = next(
                                filter(
                                    lambda x: "name" in x and x["name"] == param_name,
                                    generated_parameters,
                                )
                            )

                            param_types[param_name] = matching_param["type"]
                        except StopIteration:
                            param_types[param_name] = False
                        except KeyError:
                            param_types[param_name] = False
                        except Exception as e:
                            self.logger.exception(
                                f"An unkown error occurred while extracting generated type for parameter [{param_name}]",
                                exc_info=e,
                            )
                            param_types[param_name] = False

                    param_descriptions: dict[str, str | bool] = {}
                    for param_name in code_object.parameters:
                        try:
                            generated_parameters = generated_output[param_name] = generated_output[
                                "parameters"
                            ]
                            matching_param = next(
                                filter(
                                    lambda x: "name" in x and x["name"] == param_name,
                                    generated_parameters,
                                )
                            )
                            param_descriptions[param_name] = matching_param["description"]
                        except StopIteration:
                            param_descriptions[param_name] = False
                        except KeyError:
                            param_descriptions[param_name] = False
                        except Exception as e:
                            self.logger.warning(
                                f"An unkown error occurred while extracting generated description for parameter [{param_name}]",
                                exc_info=e,
                            )
                            param_descriptions[param_name] = False

                    exception_descriptions: dict[str, str | bool] = {}
                    for exception in code_object.exceptions:
                        exception_descriptions[exception] = False

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
                        parameter_types=param_types,
                        parameter_descriptions=param_descriptions,
                        return_description=return_description,
                        return_type=return_type,
                        exception_descriptions=exception_descriptions,
                    )
            except KeyboardInterrupt as e:
                # Let user aborte execution
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

    def _build_check_outdated_prompt(self, existing_docstring: str, code_content: str) -> str:
        # Followed Prompt Guidelines:
        # - https://help.openai.com/en/articles/10032626-prompt-engineering-best-practices-for-chatgpt
        # - https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-8B#usage-recommendations

        truncated_code_content = code_content[: self.context_size - len(existing_docstring) - 577]

        return f"""
You are an AI documentation assistant, and your task is to evaluate if an existing function docstring correctly describes the given code of the function.
The purpose of the documentation is to help developers and beginners understand the function and specific usage of the code.
If any part of the docstring is inadequate, consider the whole docstring to be inadequate. Any mocked docstring is to be considered inadequate.

The existing docstring is as follows:
'''
{existing_docstring}
'''

The content of the code is as follows:
'''
{truncated_code_content}
'''

Please reason step by step to find out if the existing docstring matches the code, and put your final answer within {{
    "analysis": "your analysis goes here",
    "matches": true or false
}}
<think>
"""

    def _extract_check_outdated_output(self, result: str) -> bool:
        match = re.search(CHECK_OUTDATED_JSON_OUTPUT_REGEX, result, re.DOTALL | re.IGNORECASE)

        if match is None or match.group(1) is None:
            raise ValueError("No JSON match found")

        analysis_json_str = match.group(1)
        analysis_json = json5.loads(analysis_json_str)

        return "matches" in analysis_json and analysis_json["matches"]

    def _extract_generate_docstring_output(self, result: str) -> dict:
        match = re.search(DOCSTRING_GENERATION_JSON_OUTPUT_REGEX, result, re.DOTALL | re.IGNORECASE)

        if match is None:
            raise ValueError("No JSON match found")

        analysis_json_str = match.group(0)
        analysis_json = json5.loads(analysis_json_str)

        return analysis_json
