class CodeObject():
    def __init__(self, name, filename, code_type, body, ast_tree, docstring=None, code=None, arguments=None, return_type=None, exceptions=None):
        self.name = name
        self.filename = filename
        self.type = code_type
        self.id = filename + "_" + self.type + "_" + self.name
        print(self.id)
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
        self.outdated = False
        self.is_updated = False
        self.send_to_gpt = False

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
        if hasattr(self, "docstring"):
            return self.docstring
        return None
    
    def get_code(self):
        return self.code

class ClassObject(CodeObject):
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

class MethodObject(CodeObject):
    def __init__(self, name, filename, signature, body, ast_tree, class_obj_id=None, module_obj_id=None, docstring=None, code=None, arguments=None, return_type=None, exceptions=None):
        self.signature = signature
        self.class_obj_id = class_obj_id
        self.module_obj_id = module_obj_id
        self.missing_arg_types = []
        self.missing_return_type = False
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
    
    def get_missing_arg_types(self):
        return self.missing_arg_types


class CodeRepresenter():
    def __init__(self):
        self.objects = {}
    
    def get(self, id):
        if id in self.objects.keys():
            return self.objects[id]
        raise KeyError
    
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
            return [argument for argument in self.objects[code_obj_id].arguments if argument["name"] != "self"] # ignore self
        return None

    def get_return_type(self, code_obj_id):
        if code_obj_id in self.objects.keys() and hasattr(self.objects[code_obj_id], "return_type"):
            return self.objects[code_obj_id].return_type
        return None

    def get_exceptions(self, code_obj_id):
        if code_obj_id in self.objects.keys() and hasattr(self.objects[code_obj_id], "exceptions"):
            return self.objects[code_obj_id].exceptions
        return None

    def get_missing_arg_types(self, code_obj_id):
        code_obj = self.objects[code_obj_id]
        if not isinstance(code_obj, MethodObject):
            return False
        return code_obj.get_missing_arg_types()

    def return_types_missing(self, code_obj_id):
        code_obj = self.objects[code_obj_id]
        if not isinstance(code_obj, MethodObject):
            return False
        return code_obj.missing_return_type
    
    def get_extract_args_types_exceptions(self, code_obj_id):
        return {"arguments": self.get_arguments(code_obj_id=code_obj_id),
                "return_type": self.get_return_type(code_obj_id=code_obj_id),
                "exceptions": self.get_exceptions(code_obj_id=code_obj_id),
                "missing_arg_types": self.get_missing_arg_types(code_obj_id=code_obj_id),
                "return_type_missing": self.return_types_missing(code_obj_id=code_obj_id),
                }

    def get_by_filename(self, filename: str):
        if not filename.endswith(".py"):
            filename += ".py"
        matches = []
        for object in self.objects.values():
            if object.filename == filename:
                matches.append(object)
        return matches

    def get_context_docstrings(self, id):
        code_obj = self.get(id)
        tmp = code_obj.get_context()
        tmp.pop("class_obj_id", None)
        tmp.pop("module_obj_id", None)
        keys = []
        for sub_list in tmp.values():
            keys.extend(sub_list)
        keys.append(code_obj.class_obj_id)
        keys.append(code_obj.module_obj_id)
        result = {}
        for key in keys:
            if key is None:
                continue
            code_obj_2 = self.get(key)
            if hasattr(code_obj_2, "docstring"):
                result[key] = code_obj_2.docstring
            else:
                result[key] = code_obj_2.code
        return result

    def depends_on_outdated_code(self, id):
        code_obj = self.get(id)
        for code_id in code_obj.called_classes:
            if self.get(code_id).outdated:
                return True
        for code_id in code_obj.called_methods:
            if self.get(code_id).outdated:
                return True
        if hasattr(code_obj, "class_obj_id") and code_obj.class_obj_id is not None:
            if self.get(code_obj.class_obj_id).outdated:
                return True
        if hasattr(code_obj, "module_obj_id") and code_obj.module_obj_id is not None:
            if self.get(code_obj.module_obj_id).outdated:
                return True
        return False
    
    def update_docstring(self, id, new_docstring):
        code_obj = self.get(id)
        code_obj.old_docstring = code_obj.docstring
        code_obj.docstring = new_docstring
        code_obj.is_updated = True
        code_obj.outdated = False