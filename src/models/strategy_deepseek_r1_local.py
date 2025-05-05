import re

import json5
from gpt4all import GPT4All

import gpt_input
from gpt_input import (
    GptInputCodeObject,
    GptOutput,
    GptOutputClass,
    GptOutputMethod,
    GptOutputModule,
)
from models.prompt_builder.deepseek_r1_prompt_builder import DeepseekR1PromptBuilder
from save_data import save_data

from .model_strategy import DocstringModelStrategy

CHECK_OUTDATED_JSON_OUTPUT_REGEX = (
    r'({\s*"analysis":\s*"(.*)"\s*,\s*"matches"\s*:\s*(true|false)\s*})'
)
DOCSTRING_GENERATION_JSON_OUTPUT_REGEX = r"{[^`]+}"


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
