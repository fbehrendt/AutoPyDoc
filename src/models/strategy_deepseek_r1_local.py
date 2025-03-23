import re

import json5
from gpt4all import GPT4All

from gpt_input import (
    GptInputCodeObject,
    GptInputMethodObject,
    GptOutput,
    GptOutputMethod,
)

from .model_factory import ModelStrategyFactory
from .model_strategy import DocstringModelStrategy

CHECK_OUTDATED_JSON_OUTPUT_REGEX = (
    r'({\s*"analysis":\s*"(.*)"\s*,\s*"matches"\s*:\s*(true|false)\s*})'
)
DOCSTRING_GENERATION_JSON_OUTPUT_REGEX = r"{.*}"


class LocalDeepseekR1Strategy(DocstringModelStrategy):
    def __init__(self, device="cuda", context_size=2048):
        super().__init__()

        # TODO: remove temp workaround
        self.fallback_stategy = ModelStrategyFactory.create_strategy("mock")

        self.device = device
        self.context_size = context_size

        self.empty_prompt_length = 0
        self.empty_prompt_length = len(self._build_generate_docstring_prompt(""))
        self.logger.debug("Empty prompt length [%d]", self.empty_prompt_length)

        model_name = "DeepSeek-R1-Distill-Llama-8B-Q4_0.gguf"

        self.logger.info(
            "Using GPT4All model [%s] with context size [%d]",
            model_name,
            self.context_size,
        )
        self.gpt_model = GPT4All(model_name=model_name, device=self.device)

        self.logger.info(
            "Using device [%s], requested [%s]", self.gpt_model.device, self.device
        )

        if self.gpt_model.device is None:
            raise Exception("Unable to load gpt model")

    def check_outdated(self, code_object: GptInputCodeObject) -> bool:
        try:
            with self.gpt_model.chat_session():
                prompt = self._build_check_outdated_prompt(
                    code_object.docstring, code_object.code
                )

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

                self.logger.info(
                    "Finished checking existing docstring [%s]", generated_text
                )

                docstring_matches = self._extract_check_outdated_output(generated_text)

                return not docstring_matches
        except Exception as e:
            self.logger.exception(
                "An error occurred while checking existing docstring", exc_info=e
            )
            raise e

    def generate_docstring(self, code_object: GptInputCodeObject) -> GptOutput:
        if isinstance(code_object, GptInputMethodObject):
            try:
                with self.gpt_model.chat_session():
                    prompt = self._build_generate_docstring_prompt(code_object.code)

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

                    self.logger.info(
                        "Finished docstring generation [%s]", generated_text
                    )

                    generated_output = self._extract_generate_docstring_output(
                        generated_text
                    )

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
                            generated_parameters = generated_output[param_name] = (
                                generated_output["parameters"]
                            )
                            matching_param = next(
                                filter(
                                    lambda x: "name" in x and x["name"] == param_name,
                                    generated_parameters,
                                )
                            )
                            param_descriptions[param_name] = matching_param[
                                "description"
                            ]
                        except StopIteration:
                            param_descriptions[param_name] = False
                        except KeyError:
                            param_descriptions[param_name] = False
                        except Exception as e:
                            self.logger.exception(
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

    def _build_check_outdated_prompt(
        self, existing_docstring: str, code_content: str
    ) -> str:
        # Followed Prompt Guidelines:
        # - https://help.openai.com/en/articles/10032626-prompt-engineering-best-practices-for-chatgpt
        # - https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-8B#usage-recommendations

        truncated_code_content = code_content[
            : self.context_size - len(existing_docstring) - 577
        ]

        return f"""
You are an AI documentation assistant, and your task is to evaluate if an existing function docstring correctly describes the given code of the function.
The purpose of the documentation is to help developers and beginners understand the function and specific usage of the code.

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
        match = re.search(
            CHECK_OUTDATED_JSON_OUTPUT_REGEX, result, re.DOTALL | re.IGNORECASE
        )

        if match is None or match.group(1) is None:
            raise ValueError("No JSON match found")

        analysis_json_str = match.group(1)
        analysis_json = json5.loads(analysis_json_str)

        return "matches" in analysis_json and analysis_json["matches"]

    def _build_generate_docstring_prompt(
        self, code_content: str, language="english"
    ) -> str:
        max_code_length = self.context_size - self.empty_prompt_length
        self.logger.debug("Code length [%d/%d]", len(code_content), max_code_length)
        truncated_code_content = code_content[:max_code_length]

        prompt = f"""
You are an AI documentation assistant, and your task is to analyze the code of a Python function.
The purpose of the analysis is to help developers and beginners understand the function and specific usage of the code.
Use plain text (including all details), in language {language} in a deterministic tone.

The content of the code is as follows:
'''
{truncated_code_content}
'''

Please note:
- Write mainly in the {
            language
        } language. If necessary, you can write with some English words in the analysis and description to enhance the document's readability because you do not need to translate the function name or variable name into the target language.
- Keep the text short and concise, and avoid unnecessary details.
- Keep in mind that your audience is document readers, so use a deterministic tone to generate precise content and don't let them know you're provided with code snippet and documents.
- AVOID ANY SPECULATION and inaccurate descriptions!
- DO NOT use markdown syntax in the output

Now, provide the documentation for the target object in {
            language
        } in a professional way.
Please reason step by step, and always summarize your final answer using the following json format {{
    "description": "your docstring description goes here",
    "parameters": [
        {{"name": "parameter name", "type": "parameter type", "description": "description for this parameter"}},
        for each parameter
    ],
    "returns": {{"type": "return type", "description": "description for this return value"}}
}}. Stick to this format WITHOUT EXCEPTIONS.

Here is an example of the expected output format:
{{"description": "Extract start, end and content of methods affected by change information",
    "parameters": [
        {{
            "name": "filename",
            "type": "str",
            "description": "File to extract mehod information from"
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

<think>
"""
        print("Generated Prompt", len(prompt))
        return prompt

    # TODO: add exception description output
    # TODO: try explicit unkown type

    def _extract_generate_docstring_output(self, result: str) -> dict:
        match = re.search(
            DOCSTRING_GENERATION_JSON_OUTPUT_REGEX, result, re.DOTALL | re.IGNORECASE
        )

        if match is None:
            raise ValueError("No JSON match found")

        analysis_json_str = match.group(0)
        analysis_json = json5.loads(analysis_json_str)

        return analysis_json
