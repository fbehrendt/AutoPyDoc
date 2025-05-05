import logging
from typing import Iterable, Optional

from gpt_input import (
    GptInputClassObject,
    GptInputCodeObject,
    GptInputMethodObject,
    GptInputModuleObject,
)


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
Provided context shall be used to better understand what the class does and does not need to be analyzed further than that.
Do not generate descriptions for methods and subclasses.

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
