class Code_obj():
    def __init__(self, name, filename, code_type, body, ast_tree, docstring=None, code=None, arguments=None, return_type=None, exceptions=None):
        self.name = name
        self.filename = filename
        self.type = code_type
        self.id = filename + "_" + self.type + "_" + self.name
        self.body = body
        if docstring:
            self.docstring = docstring
        self.ast_tree=ast_tree
        if code:
            self.code = code
        if arguments:
            self.arguments = arguments
        self.ast_tree=ast_tree
        if return_type:
            self.return_type = return_type
        if exceptions:
            self.exceptions = exceptions
        self.called_methods = []
        self.called_classes = []
        self.called_by_methods = []
        self.called_by_classes = []
        self.called_by_modules = []
        self.exceptions = []
        self.missing_arg_types = []
    
    def add_called_method(self, called_method_id):
        self.called_methods.append(called_method_id)
    
    def add_called_class(self, called_class_id):
        self.called_classes.append(called_class_id)

    def add_caller_method(self, caller_method_id):
        self.called_by_methods.append(caller_method_id)
    
    def add_caller_class(self, caller_class_id):
        self.called_by_classes.append(caller_class_id)
    
    def add_caller_module(self, caller_module_id):
        self.called_by_modules.append(caller_module_id)

    def add_docstring(self, docstring):
        self.docstring = docstring
    
    def add_ast(self, ast):
        self.ast = ast
    
    def add_code(self, code):
        self.code = code

    def get_context(self):
        return {
            "called_methods": self.called_methods,
            "called_classes": self.called_classes,
            "called_by_methods": self.called_by_methods,
            "called_by_classes": self.called_by_classes,
            "called_by_modules": self.called_by_modules,
        }
    
    def add_exception(self, exception):
        self.exceptions.append(exception)

    def get_docstring(self):
        return self.docstring
    
    def get_code(self):
        return self.code

class Class_obj(Code_obj):
    def __init__(self, name, filename, signature, body, ast_tree, class_obj_id=None, module_obj_id=None, docstring=None, code=None, arguments=None, return_type=None, exceptions=None):
        self.signature = signature
        self.class_obj_id = class_obj_id
        self.module_obj_id = module_obj_id
        super().__init__(name, filename, "class", body=body, ast_tree=ast_tree, docstring=docstring, code=code, arguments=arguments, return_type=return_type, exceptions=exceptions)

    def add_module(self, module_obj):
        self.module_obj = module_obj
    
    def get_context(self):
        result = super().get_context()
        result["class_obj_id"] = self.class_obj_id
        result["module_obj_id"] = self.module_obj_id
        return result

class Method_obj(Code_obj):
    def __init__(self, name, filename, signature, body, ast_tree, class_obj_id=None, module_obj_id=None, docstring=None, code=None, arguments=None, return_type=None, exceptions=None):
        self.signature = signature
        self.class_obj_id = class_obj_id
        self.module_obj_id = module_obj_id
        super().__init__(name, filename, "method", body, ast_tree, docstring=docstring, code=code, arguments=arguments, return_type=return_type, exceptions=exceptions)

    def add_module(self, module_obj_id):
        self.module_obj_id = module_obj_id
    
    def add_class(self, class_obj):
        self.class_obj = class_obj
    
    def get_context(self):
        result = super().get_context()
        result["class_obj_id"] = self.class_obj_id
        result["module_obj_id"] = self.module_obj_id
        return result
        
    def add_missing_arg_type(self, arg_name):
        self.missing_arg_types.append(arg_name)

class CodeRepresenter():
    def __init__(self):
        self.objects = {}
    
    def add_code_obj(self, code_obj):
        if code_obj.id not in self.objects:
            self.objects[code_obj.id] = code_obj
    
    def get_docstring(self, code_obj_id):
        if code_obj_id in self.objects.keys() and hasattr(self.objects[code_obj_id], "docstring"):
            return self.objects[code_obj_id].docstring
        return None

    def get_code(self, code_obj_id):
        if code_obj_id in self.objects.keys() and hasattr(self.objects[code_obj_id], "code"):
            return self.objects[code_obj_id].code
        return None

    def get_arguments(self, code_obj_id):
        if code_obj_id in self.objects.keys() and hasattr(self.objects[code_obj_id], "arguments"):
            return self.objects[code_obj_id].arguments
        return None

    def get_return_type(self, code_obj_id):
        if code_obj_id in self.objects.keys() and hasattr(self.objects[code_obj_id], "return_type"):
            return self.objects[code_obj_id].return_type
        return None

    def get_exceptions(self, code_obj_id):
        if code_obj_id in self.objects.keys() and hasattr(self.objects[code_obj_id], "exceptions"):
            return self.objects[code_obj_id].exceptions
        return None
    
    def get_extract_args_types_exceptions(self, code_obj_id):
        return {"arguments": self.get_arguments(code_obj_id=code_obj_id),
                "return_type": self.get_return_type(code_obj_id=code_obj_id),
                "exceptions": self.get_exceptions(code_obj_id=code_obj_id),}
