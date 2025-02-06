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
        if self.return_type or self.return_description:
            docstring += ' '* self.indentation_level + f':return: {self.return_description}\n'
            docstring += ' '* self.indentation_level + f':rtype: {self.return_type}\n\n'
        for exception in self.exceptions:
            docstring += ' '* self.indentation_level + f':raises {exception["name"]}: {exception["description"]}\n'
        if len(self.exceptions) > 0:
            docstring += '\n'
        docstring += ' '* self.indentation_level + '"""'
        return docstring
