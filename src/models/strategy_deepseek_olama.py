from base64 import b64encode
from urllib.parse import urlparse, urlunparse

from ollama import Client

import gpt_input
import helpers
from gpt_input import (
    GptInputCodeObject,
    GptOutput,
    GptOutputClass,
    GptOutputMethod,
    GptOutputModule,
)
from models.prompt_builder.deepseek_r1_prompt_builder import DeepseekR1PromptBuilder

from .model_strategy import DocstringModelStrategy


class OllamaDeepseekR1Strategy(DocstringModelStrategy):
    def __init__(self, context_size=2048, ollama_host=None):
        super().__init__()

        # TODO: remove temp workaround
        # self.fallback_stategy = ModelStrategyFactory.create_strategy("mock")

        self.context_size = context_size

        self.prompt_builder = DeepseekR1PromptBuilder(context_size)

        self.model_name = "deepseek-r1:8b"

        self.logger.info(
            "Using Ollama model [%s] with context size [%d]",
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
            self.logger.info("Start checking existing docstring")

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

                stream = self.client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    format={
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "parameters": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                        },
                                        "type": {
                                            "type": "string",
                                        },
                                        "description": {
                                            "type": "string",
                                        },
                                    },
                                    "required": ["name", "type", "description"],
                                },
                            },
                            "exceptions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "exception_class": {
                                            "type": "string",
                                        },
                                        "description": {
                                            "type": "string",
                                        },
                                    },
                                    "required": ["exception_class", "description"],
                                },
                            },
                            "returns": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                    },
                                    "description": {
                                        "type": "string",
                                    },
                                },
                                "required": ["type", "description"],
                            },
                        },
                        "required": ["description", "parameters", "exceptions", "returns"],
                    },
                    stream=True,
                    options={"num_ctx": self.context_size, "temperature": 0.6},
                )

                generated_text = ""

                for chunk in stream:
                    print(chunk["response"], end="", flush=True)
                    generated_text += chunk["response"]

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
                        matching_parameters = next(
                            filter(
                                lambda x: "name" in x and x["name"] == parameter_name,
                                generated_parameters,
                            )
                        )

                        parameter_types[parameter_name] = matching_parameters["type"]
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
                        generated_parameters = generated_output["parameters"]
                        matching_parameters = next(
                            filter(
                                lambda x: "name" in x and x["name"] == parameter_name,
                                generated_parameters,
                            )
                        )
                        parameter_descriptions[parameter_name] = matching_parameters["description"]
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
                        matching_exception = next(
                            filter(
                                lambda x: "name" in x and x["name"] == parameter_name,
                                generated_exceptions,
                            )
                        )
                        exception_descriptions[exception] = matching_exception["description"]
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
                    validationerror=False,
                    generationerror=False,
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
                    format={
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "class_attributes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                        },
                                        "type": {
                                            "type": "string",
                                        },
                                        "description": {
                                            "type": "string",
                                        },
                                    },
                                    "required": ["name", "type", "description"],
                                },
                            },
                            "instance_attributes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                        },
                                        "type": {
                                            "type": "string",
                                        },
                                        "description": {
                                            "type": "string",
                                        },
                                    },
                                    "required": ["name", "type", "description"],
                                },
                            },
                        },
                        "required": ["description", "class_attributes", "instance_attributes"],
                    },
                    stream=True,
                    options={"num_ctx": self.context_size, "temperature": 0.6},
                )

                generated_text = ""

                for chunk in stream:
                    print(chunk["response"], end="", flush=True)
                    generated_text += chunk["response"]

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
                    validationerror=False,
                    generationerror=False,
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
                    format={
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "exceptions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "exception_class": {
                                            "type": "string",
                                        },
                                        "description": {
                                            "type": "string",
                                        },
                                    },
                                    "required": ["exception_class", "description"],
                                },
                            },
                        },
                        "required": ["description", "parameters"],
                    },
                    stream=True,
                    options={"num_ctx": self.context_size, "temperature": 0.6},
                )

                generated_text = ""

                for chunk in stream:
                    generated_text += chunk["response"]

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
                        matching_exception_class = next(
                            filter(
                                lambda x: "exception_class" in x
                                and x["exception_class"] == exception_class,
                                generated_exceptions,
                            )
                        )

                        exception_descriptions[exception_class] = matching_exception_class[
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
                    validationerror=False,
                    generationerror=False,
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
        try:
            analysis_json = helpers.parse_first_json_object(result)
        except ValueError:
            raise ValueError("No JSON match found")

        return "matches" in analysis_json and analysis_json["matches"]

    def _extract_generate_docstring_json_output(self, result: str) -> dict:
        try:
            return helpers.parse_first_json_object(result)
        except ValueError:
            raise ValueError("No JSON match found")


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
