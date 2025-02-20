class DocstringBuilder():
    def __init__(self, indentation_level: int) -> None:
        self.indentation_level = indentation_level
        self.params = []
        self.exceptions = []
    
    def add_description(self, description: str) -> None:
        self.description = description
    
    def add_param(self, param_name: str, param_description: str, param_type: str, param_default: str=None) -> None:
        param = {
            "name": param_name,
            "description": param_description,
            "type": param_type,
        }
        if param_default is not None:
            param["default"] = param_default
        self.params.append(param)
    
    def add_exception(self, exception_name: str, exception_description: str) -> None:
        self.exceptions.append({
            "name": exception_name,
            "description": exception_description
        })

    def add_return(self, return_description: str, return_type: str) -> None:
        self.return_description = return_description
        self.return_type = return_type
    
    def build(self) -> str:
        docstring = ' '* self.indentation_level + '"""'
        docstring += self.description + '\n'
        if len(self.params) > 0:
            docstring += '\n'
        for param in self.params:
            docstring += ' '* self.indentation_level + f':param {param["name"]}: {param["description"]}\n'
            if "default" in param.keys():
                docstring += ' ' + f' Default is {param["default"]}\n'
            docstring += ' '* self.indentation_level + f':type {param["name"]}: {param["type"]}\n'
        if len(self.params) >  0:
            docstring += '\n'
        if hasattr(self, "return_type") and hasattr(self, "return_description"):
            docstring += ' '* self.indentation_level + f':return: {self.return_description}\n'
            docstring += ' '* self.indentation_level + f':rtype: {self.return_type}\n\n'
        for exception in self.exceptions:
            docstring += ' '* self.indentation_level + f':raises {exception["name"]}: {exception["description"]}\n'
        if len(self.exceptions) > 0:
            docstring += '\n'
        docstring += ' '* self.indentation_level + '"""'
        return docstring

def create_docstring(code_obj, result, indentation_level, debug=False):
    docstring_builder = DocstringBuilder(indentation_level=indentation_level)
    if not debug:
        raise NotImplementedError
    docstring_builder.add_description(result["description"]) # TODO
    if code_obj.type == "method":
        for param in code_obj.arguments:
            if param["name"] == "self": # skip self
                continue
            if param["name"] in result["parameter_types"].keys():
                param_type = result["parameter_types"][param["name"]]
            else:
                param_type = param["type"]
            if "default" in param.keys():
                docstring_builder.add_param(param_name=param["name"], param_type=param_type, param_default=param["default"], param_description=result["parameter_descriptions"][param["name"]]) # TODO
            else:
                docstring_builder.add_param(param_name=param["name"], param_type=param_type, param_description=result["parameter_descriptions"][param["name"]]) # TODO
        for exception, exception_description in result["exception_descriptions"].items():
            docstring_builder.add_exception(exception_name=exception, exception_description=exception_description) # TODO
        if not code_obj.missing_return_type and code_obj.return_type is not None:
            if "return type" in result.keys():
                return_type = result["return type"]
            else:
                return_type = code_obj.return_type
            docstring_builder.add_return(return_type=return_type, return_description=result["return_description"]) # TODO
    elif code_obj.type == "class":
        if not debug:
            raise NotImplementedError
        pass
    else:
        raise NotImplementedError # TODO
    return docstring_builder.build()