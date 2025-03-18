import re

class DocstringUnBuilder:
  def __init__(self, docstring: str):
      self.docstring = docstring
      
      self.description_pattern = r'"""\n?[ ]*([^:]+)(?::param|:return|:raises|:class attribute|:instance attribute)'
      
      self.func_param_pattern = r"\n[ ]*:param (\w+): (\N+)\n[ ]*:type (\w+): (\N+)"
      self.func_param_name_pattern = r"\n[ ]*:param (\w+):"
      self.func_param_description_pattern = r"\n[ ]*:param \w+: (\N+)"
      self.func_param_type_pattern = r"\n[ ]*:param \w+: \N+\n[ ]*:type \w+: (\N+)"

      self.func_return_pattern = r"\n[ ]*:return: (\N+)\n[ ]*:rtype: (\N+)"
      
      self.func_return_description_pattern = r"\n[ ]*:return: (\N+)"
      self.func_return_type_pattern = r"\n[ ]*:rtype: (\N+)"
      
      self.exception_pattern = r"\n[ ]*:raises (\w+): (\N+)"
      self.exception_name_pattern = r"\n[ ]*:raises (\w+): \N+"
      self.exception_description_pattern = r"\n[ ]*:raises \w+: (\N+)"

      self.class_attr_pattern = r"\n[ ]*:class attribute (\w+): (\N+)\n[ ]*:type (\w+): (\N+)"
      self.class_attr_name_pattern = r"\n[ ]*:class attribute (\w+): \N+"
      self.class_attr_description_pattern = r"\n[ ]*:class attribute \w+: (\N+)"
      self.class_attr_type_pattern = r"\n[ ]*:class attribute \w+: \N+\n[ ]*:type \w+: (\N+)"

      self.instance_attr_pattern = r"\n[ ]*:instance attribute (\w+): (\N+)\n[ ]*:type (\w+): (\N+)"
      self.instance_attr_name_pattern = r"\n[ ]*:instance attribute (\w+): \N+"
      self.instance_attr_description_pattern = r"\n[ ]*:instance attribute \w+: (\N+)"
      self.instance_attr_type_pattern = r"\n[ ]*:instance attribute \w+: \N+\n[ ]*:type \w+: (\N+)"

      self.description = self.apply_pattern(self.description_pattern)
      self.params = self.apply_pattern(self.func_param_pattern)
      self.return_info = self.apply_pattern(self.func_return_pattern)
      self.exceptions = self.apply_pattern(self.exception_pattern)
      self.class_attrs = self.apply_pattern(self.class_attr_pattern)
      self.instance_attrs = self.apply_pattern(self.instance_attrs)

      print("Description", self.description)
      print("params", self.params)
      print("return", self.return_info)
      print("exceptions", self.exceptions)
      print("class attrs", self.class_attrs)
      print("instance attrs", self.instance_attrs)

  def apply_pattern(self, pattern):
      pattern = re.compile(pattern)
      return re.findall(pattern, self.docstring)
  
docstring1 = '"""\n    Create a docstring for a CodeObject, using the GPT results\n\n    :param code_obj: CodeObject in question\n    :type code_obj: CodeObject\n    :param result: the 1 GPT results,.;:\n    :type result: dict\n    :param indentation_level: indentation level the docstring should have\n    :type indentation_level: int\n    :param debug: toggle debug mode. Default False\n    :type debug: bool\n\n    :return: docstring for the CodeObject\n    :rtype: str\n\n    :raises NotImplementedError: raised when trying to access functionality that is not yet implemented\n\n    :class attribute filename: description for class attr filename\n    :type filename: str\n    :instance attribute filename: description for instance attr filename\n    :type filename: str\n"""'

if __name__ == "__main__":
  docstring_unbuilder = DocstringUnBuilder(docstring=docstring1)