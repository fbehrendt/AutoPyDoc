import re

import json5
from google import genai
from google.genai import types

import gpt_input
from gpt_input import (
    GptInputCodeObject,
    GptOutput,
    GptOutputClass,
    GptOutputMethod,
    GptOutputModule,
)
from models.prompt_builder.deepseek_r1_prompt_builder import DeepseekR1PromptBuilder

from .model_strategy import DocstringModelStrategy

CHECK_OUTDATED_JSON_OUTPUT_REGEX = (
    r'({\s*"analysis":\s*"(.*)"\s*,\s*"matches"\s*:\s*(true|false)\s*})'
)
DOCSTRING_GENERATION_JSON_OUTPUT_REGEX = r"{.+}"


class GoogleGeminiStrategy(DocstringModelStrategy):
    def __init__(self, context_size=2048, gemini_api_key=None):
        super().__init__()

        # TODO: remove temp workaround
        # self.fallback_stategy = ModelStrategyFactory.create_strategy("mock")

        self.context_size = context_size

        self.prompt_builder = DeepseekR1PromptBuilder(context_size)

        self.model_name = "gemini-2.0-flash-lite"

        self.logger.info(
            "Using Google Gemini model [%s] with context size [%d]",
            self.model_name,
            self.context_size,
        )

        self.client = genai.Client(
            api_key=gemini_api_key,
        )

    def check_outdated(self, code_object: GptInputCodeObject) -> bool:
        try:
            prompt = self.prompt_builder.build_check_outdated_prompt(code_object)

            self.logger.debug("Using prompt [%s]", prompt)
            self.logger.info("Starting checking existing docstring")

            stream = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=prompt),
                        ],
                    ),
                ],
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=0,
                    ),
                    response_mime_type="application/json",
                    # response_schema=genai.types.Schema(
                    #     type=genai.types.Type.OBJECT,
                    #     properties={
                    #         "analysis": genai.types.Schema(
                    #             type=genai.types.Type.STRING,
                    #         ),
                    #         "matches": genai.types.Schema(
                    #             type=genai.types.Type.BOOLEAN,
                    #         ),
                    #     },
                    # ),
                ),
            )

            generated_text = ""

            for chunk in stream:
                print(chunk.text, end="", flush=True)
                generated_text += chunk.text

            self.logger.debug("Finished checking existing docstring [%s]", generated_text)

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

                stream = self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_text(text=prompt),
                            ],
                        ),
                    ],
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(
                            thinking_budget=0,
                        ),
                        response_mime_type="application/json",
                        # response_schema=genai.types.Schema(
                        #     type=genai.types.Type.OBJECT,
                        #     properties={
                        #         "description": genai.types.Schema(
                        #             type=genai.types.Type.STRING,
                        #         ),
                        #         "parameters": genai.types.Schema(
                        #             type=genai.types.Type.ARRAY,
                        #             items=genai.types.Schema(
                        #                 type=genai.types.Type.OBJECT,
                        #                 properties={
                        #                     "name": genai.types.Schema(
                        #                         type=genai.types.Type.STRING
                        #                     ),
                        #                     "type": genai.types.Schema(
                        #                         type=genai.types.Type.STRING
                        #                     ),
                        #                     "description": genai.types.Schema(
                        #                         type=genai.types.Type.STRING
                        #                     ),
                        #                 },
                        #             ),
                        #         ),
                        #         "returns": genai.types.Schema(
                        #             type=genai.types.Type.OBJECT,
                        #             properties={
                        #                 "type": genai.types.Schema(type=genai.types.Type.STRING),
                        #                 "description": genai.types.Schema(
                        #                     type=genai.types.Type.STRING
                        #                 ),
                        #             },
                        #         ),
                        #     },
                        # ),
                    ),
                )

                generated_text = ""

                for chunk in stream:
                    print(chunk.text, end="", flush=True)
                    generated_text += chunk.text

                self.logger.debug("Finished docstring generation [%s]", generated_text)

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
                        generated_exceptions = generated_output["exceptions"]
                        matching_instance_attribute = next(
                            filter(
                                lambda x: "name" in x and x["name"] == parameter_name,
                                generated_exceptions,
                            )
                        )
                        exception_descriptions[exception] = matching_instance_attribute[
                            "description"
                        ]
                    except StopIteration:
                        exception_descriptions[exception] = False
                    except KeyError:
                        exception_descriptions[exception] = False
                    except Exception as e:
                        self.logger.warning(
                            f"An unkown error occurred while extracting generated description for exception [{exception}]",
                            exc_info=e,
                        )
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
                self.logger.debug("Starting docstring generation")

                stream = self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_text(text=prompt),
                            ],
                        ),
                    ],
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(
                            thinking_budget=0,
                        ),
                        response_mime_type="application/json",
                        # response_schema=genai.types.Schema(
                        #     type=genai.types.Type.OBJECT,
                        #     properties={
                        #         "description": genai.types.Schema(type=genai.types.Type.STRING),
                        #         "class_attributes": genai.types.Schema(
                        #             type=genai.types.Type.ARRAY,
                        #             items=genai.types.Schema(
                        #                 type=genai.types.Type.OBJECT,
                        #                 properties={
                        #                     "name": genai.types.Schema(
                        #                         type=genai.types.Type.STRING
                        #                     ),
                        #                     "type": genai.types.Schema(
                        #                         type=genai.types.Type.STRING
                        #                     ),
                        #                     "description": genai.types.Schema(
                        #                         type=genai.types.Type.STRING
                        #                     ),
                        #                 },
                        #             ),
                        #         ),
                        #         "instance_attributes": genai.types.Schema(
                        #             type=genai.types.Type.ARRAY,
                        #             items=genai.types.Schema(
                        #                 type=genai.types.Type.OBJECT,
                        #                 properties={
                        #                     "name": genai.types.Schema(
                        #                         type=genai.types.Type.STRING
                        #                     ),
                        #                     "type": genai.types.Schema(
                        #                         type=genai.types.Type.STRING
                        #                     ),
                        #                     "description": genai.types.Schema(
                        #                         type=genai.types.Type.STRING
                        #                     ),
                        #                 },
                        #             ),
                        #         ),
                        #     },
                        # ),
                    ),
                )

                generated_text = ""

                for chunk in stream:
                    print(chunk.text, end="", flush=True)
                    generated_text += chunk.text

                self.logger.debug("Finished docstring generation [%s]", generated_text)

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

                stream = self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_text(text=prompt),
                            ],
                        ),
                    ],
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(
                            thinking_budget=0,
                        ),
                        response_mime_type="application/json",
                        # response_schema=genai.types.Schema(
                        #     type=genai.types.Type.OBJECT,
                        #     properties={
                        #       TODO
                        #     },
                        # ),
                    ),
                )

                generated_text = ""

                for chunk in stream:
                    generated_text += chunk.text

                self.logger.debug("Finished docstring generation [%s]", generated_text)

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
