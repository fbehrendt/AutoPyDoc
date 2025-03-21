import re

import json5
from gpt4all import GPT4All

from gpt_input import (
    GptInputCodeObject,
    GptInputMethodObject,
    GptOutput,
    GptOutputMethod,
)

from .model_strategy import DocstringModelStrategy

CHECK_OUTDATED_JSON_OUTPUT_REGEX = (
    r'({\s*"analysis":\s*"(.*)"\s*,\s*"matches"\s*:\s*(true|false)\s*})'
)
DOCSTRING_GENERATION_JSON_OUTPUT_REGEX = r"{.*}"


class LocalDeepseekR1Strategy(DocstringModelStrategy):
    def __init__(self, device="cuda", context_size=2048):
        super().__init__()

        self.device = device
        self.context_size = context_size

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
                    max_tokens=1000,
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

                    return GptOutputMethod(
                        id=code_object.id,
                        no_change_necessary=False,
                        description=generated_output["description"]
                        if "description" in generated_output
                        else "",
                        parameter_types={
                            p["name"]: p["type"] for p in generated_output["parameters"]
                        }
                        if "parameters" in generated_output
                        else {},
                        parameter_descriptions={
                            p["name"]: p["description"]
                            for p in generated_output["parameters"]
                        }
                        if "parameters" in generated_output
                        else {},
                        return_description=generated_output["returns"]["description"],
                        return_type=generated_output["returns"]["type"],
                        exception_descriptions={},
                        return_missing=False,  # TODO: differentiate between missing/unkown return and gpt's output attempts
                    )
            except Exception as e:
                self.logger.exception(
                    "An error occurred during docstring generation", exc_info=e
                )
                # raise e
                return GptOutput(
                    code_object.id, no_change_necessary=True, description=""
                )
        else:
            # Not Implement Yet
            return GptOutput(code_object.id, no_change_necessary=True, description="")

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
You are an AI documentation assistant, and your task is to evaluate if an existing function docstring correctly descibes the given code of the function.
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
        truncated_code_content = code_content[
            : self.context_size - len(language) * 3 - 1500
        ]

        return f"""
You are an AI documentation assistant, and your task is to analyze the code of a Python function.
The purpose of the analysis is to help developers and beginners understand the function and specific usage of the code.
Use plain text (including all details), in language {language} in a deterministic tone.

The content of the code is as follows:
'''
{truncated_code_content}
'''

Please note:
- Write mainly in the {language} language. If necessary, you can write with some English words in the analysis and description to enhance the document's readability because you do not need to translate the function name or variable name into the target language.
- Keep the text short and concise, and avoid unnecessary details.
- Keep in mind that your audience is document readers, so use a deterministic tone to generate precise content and don't let them know you're provided with code snippet and documents.
- AVOID ANY SPECULATION and inaccurate descriptions!
- DO NOT use markdown syntax in the output

Now, provide the documentation for the target object in {language} in a professional way.
Please reason step by step, and put your final answer within the following json format {{
    "description": "your docstring description goes here",
    "parameters": [
        {{"name": "parameter name", "type": "parameter type", "description": "description for this parameter"}},
        for each parameter
    ],
    "returns": {{"type": "return type", "description": "description for this return value"}}
}}. Stick to this format WITHOUT EXCEPTIONS.

<think>
"""

    def _extract_generate_docstring_output(self, result: str) -> dict:
        match = re.search(
            DOCSTRING_GENERATION_JSON_OUTPUT_REGEX, result, re.DOTALL | re.IGNORECASE
        )

        if match is None:
            raise ValueError("No JSON match found")

        analysis_json_str = match.group(0)
        analysis_json = json5.loads(analysis_json_str)

        return analysis_json
