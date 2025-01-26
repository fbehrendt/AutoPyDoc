import re

changed_method = "def get_context(self, code_obj) -> list[dict]:\nself.function_dependencies.get_function_context()\nprint("

pattern = re.compile('def ([^\(]+)')
print(re.findall(pattern, changed_method)[0])