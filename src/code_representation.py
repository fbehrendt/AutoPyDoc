import ast

class CodeObject():
    """
    Represent a piece of code like a module, class or method
    """
    def __init__(self, name: str, filename: str, code_type: str, body: list, ast_tree: ast.Node, docstring: str=None, code: str=None, arguments: list=None, return_type: str=None, exceptions: list[str]=None):
        """
        Represent a piece of code like a module, class or method

        :param name: Name of the code piece. Usually the method or class name
        :type name: str
        :param filename: File where the code is located
        :type filename: str
        :param code_type: The kind of code. E.g. method or class
        :type code_type: str
        :param body: list of ast elements of the ast representation of this code piece
        :type body: list
        :param ast_tree: Ast representation of the code
        :type ast_tree: ast.Node
        :param docstring: Docstring of the code piece. Optional
        :type docstring: str
        :param code: Code of the code piece
        :type code: str
        :param arguments: Arguments of the code obj. Optional
        :type arguments: list
        :param return_type: Return type of the code piece. Optional
        :type return_type: str
        :param exceptions: Exceptions raised by the code piece. Optional
        :type exceptions: list(str)
        """
        self.name = name
        self.filename = filename
        self.type = code_type
        self.id = filename + "_" + self.type + "_" + self.name
        # print(self.id)
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

    def add_called_method(self, called_method_id: str):
        """
        Add a called method by its id

        :param called_method_id: id of the called method
        :type called_method_id: str
        """
        self.called_methods.append(called_method_id)
    
    def add_called_class(self, called_class_id: str):
        """
        Add a called class by its id

        :param called_class_id: id of the called class
        :type called_class_id: str
        """
        self.called_classes.append(called_class_id)

    def add_caller_method(self, caller_method_id: str):
        """
        Add a method calling this code object by its id

        :param caller_method_id: id of the calling method
        :type caller_method_id: str
        """
        self.called_by_methods.append(caller_method_id)
    
    def add_caller_class(self, caller_class_id: str):
        """
        Add a class calling this code object by its id

        :param caller_class_id: id of the calling class
        :type caller_class_id: str
        """
        self.called_by_classes.append(caller_class_id)
    
    def add_caller_module(self, caller_module_id: str):
        """
        Add a module calling this code object by its id

        :param caller_module_id: id of the calling module
        :type caller_module_id: str
        """
        self.called_by_modules.append(caller_module_id)

    def add_docstring(self, docstring: str):
        """
        Add the docstring of a code piece

        :param docstring: docstring
        :type docstring: str
        """
        self.docstring = docstring
    
    def add_ast(self, ast: ast.Node):
        """"
        Add the ast representation of a code piece
        
        :param ast: abstract syntax tree of the code piece
        :type ast: ast.Node
        """
        self.ast = ast
    
    def add_code(self, code: str):
        """
        Add the code of a code piece
        
        :param code: code of the code piece
        :type code: str
        """
        self.code = code

    def add_exception(self, exception: str):
        """
        Add an exception that is raise by this code piece
        
        :param exception: The exception that is raised
        :type exception: str
        """
        self.exceptions.append(exception)

    def get_context(self)->dict[str, list[str]]:
        """
        Get the context of a code piece
        
        :return: A dictionary of types of context, containing lists of code ids
        :return type: dict[str, list[str]]
        """
        return {
            "called_methods": self.called_methods,
            "called_classes": self.called_classes,
            "called_by_methods": self.called_by_methods,
            "called_by_classes": self.called_by_classes,
            "called_by_modules": self.called_by_modules,
        }
    
    def get_docstring(self)->str|None:
        """
        Return the docstring or None, if no docstring exists
        
        :return: docstring or None
        :return type: str|None
        """
        if hasattr(self, "docstring"):
            return self.docstring
        return None
    
    def get_code(self)->str:
        """
        Return the code itself
        
        :return: the code
        :return type: str
        """
        return self.code

class ClassObject(CodeObject):
    """Representation of a class"""
    def __init__(self, name: str, filename: str, signature: str, body: list, ast_tree: ast.Node, class_obj_id: str=None, module_obj_id: str=None, docstring: str=None, code: str=None, arguments: list=None, return_type: str=None, exceptions: list[str]=None):
        """
        Represent a class. Extends CodeObject

        :param name: Name of the code piece. Usually the method or class name
        :type name: str
        :param filename: File where the code is located
        :type filename: str
        :param signature: signature of the class
        :type signature: str
        :param body: list of elements of the ast representation of the class
        :type body: list
        :param ast_tree: Ast representation of the code
        :type ast_tree: ast.Node
        :param class_obj_id: id of the parent class, if exists. Optional
        :type class_obj_id: str|None
        :param module_obj_id: id of the module which this class is part of, if exists. Optional
        :type module_obj_id: str|None
        :param docstring: Docstring of the code piece. Optional
        :type docstring: str
        :param code: Code of the code piece
        :type code: str
        :param arguments: Arguments of the code obj. Optional
        :type arguments: list
        :param return_type: Return type of the code piece. Optional
        :type return_type: str
        :param exceptions: Exceptions raised by the code piece. Optional
        :type exceptions: list[str]
        """
        self.signature = signature
        self.class_obj_id = class_obj_id
        self.module_obj_id = module_obj_id
        super().__init__(name, filename, "class", body=body, ast_tree=ast_tree, docstring=docstring, code=code, arguments=arguments, return_type=return_type, exceptions=exceptions)

    def add_module(self, module_obj_id: str):
        """
        Add the id of the module, of which this class is a part of
        
        :param module_obj_id: id of the parent module
        :type module_obj_id: str
        """
        self.module_obj_id = module_obj_id
    
    def get_context(self)->dict[str, list[str]|str]:
        """
        Get the ids of context code pieces
        
        :return: A dictionary of types of context, containing lists of code ids or a code id
        :return type: dict[str, list[str]|str]
        """
        result = super().get_context()
        result["class_obj_id"] = self.class_obj_id
        result["module_obj_id"] = self.module_obj_id
        return result

class MethodObject(CodeObject):
    """Represent a method. Extends CodeObject"""
    def __init__(self, name: str, filename: str, signature: str, body: list, ast_tree: ast.Node, class_obj_id: str=None, module_obj_id: str=None, docstring: str=None, code: str=None, arguments: list=None, return_type: str=None, exceptions: list=None):
        """
        Represent a method. Extends CodeObject

        :param name: Name of the code piece. Usually the method or class name
        :type name: str
        :param filename: File where the code is located
        :type filename: str
        :param signature: signature of the class
        :type signature: str
        :param body: list of elements of the ast representation of the class
        :type body: list
        :param ast_tree: Ast representation of the code
        :type ast_tree: ast.Node
        :param class_obj_id: id of the parent class, if exists. Optional
        :type class_obj_id: str|None
        :param module_obj_id: id of the module which this class is part of, if exists. Optional
        :type module_obj_id: str|None
        :param docstring: Docstring of the code piece. Optional
        :type docstring: str
        :param code: Code of the code piece
        :type code: str
        :param arguments: Arguments of the code obj. Optional
        :type arguments: list
        :param return_type: Return type of the code piece. Optional
        :type return_type: str
        :param exceptions: Exceptions raised by the code piece. Optional
        :type exceptions: list[str]
        """
        self.signature = signature
        self.class_obj_id = class_obj_id
        self.module_obj_id = module_obj_id
        self.missing_arg_types = []
        self.missing_return_type = False
        super().__init__(name, filename, "method", body, ast_tree, docstring=docstring, code=code, arguments=arguments, return_type=return_type, exceptions=exceptions)

    def add_module(self, module_obj_id: str):
        """
        Add the id of the module, of which this class is a part of
        
        :param module_obj_id: id of the parent module
        :type module_obj_id: str
        """
        self.module_obj_id = module_obj_id
    
    def add_class(self, class_obj: str):
        """
        Add the id of the class, of which this class is a part of
        
        :param class_obj_id: id of the parent class
        :type class_obj_id: str
        """
        self.class_obj = class_obj
    
    def get_context(self)->dict[str, list[str]|str]:
        """
        Get the ids of context code pieces
        
        :return: A dictionary of types of context, containing lists of code ids or a code id
        :return type: dict[str, list[str]|str]
        """
        result = super().get_context()
        result["class_obj_id"] = self.class_obj_id
        result["module_obj_id"] = self.module_obj_id
        return result
            
    def add_missing_arg_type(self, arg_name: str):
        """
        Add an argument for which the return type is missing
        
        :param arg_name: Name of the argument for which type information is missing
        :type arg_name: str
        """
        self.missing_arg_types.append(arg_name)
    
    def get_missing_arg_types(self)->list[str]:
        """
        Get a list of arguments, for which the return type is missing
        
        :return: list of arguments, for which the return type is missing
        :return type: list[str]
        """
        return self.missing_arg_types


class CodeRepresenter():
    """Represent all code pieces like modules, classes and methods"""
    def __init__(self):
        """Represent all code pieces like modules, classes and methods"""
        self.objects = {}
    
    def get(self, id: str)->CodeObject:
        """
        Get a CodeObject by id
        
        :param id: id of the targeted CodeObject
        :type id: str
        
        :returns: CodeObject with the passed id
        :return type: CodeObject
        """
        if id in self.objects.keys():
            return self.objects[id]
        raise KeyError
    
    def add_code_obj(self, code_obj: CodeObject):
        """
        Add a CodeObject
        
        :param code_obj: CodeObject to be added
        :type code_object: CodeObject
        """
        if code_obj.id not in self.objects:
            self.objects[code_obj.id] = code_obj
    
    def get_docstring(self, code_obj_id: str)->str|None:
        """
        Get the docstring of a CodeObject, if exists
        
        :param code_obj_id: CodeObject id
        :type code_obj_id: str

        :return: docstring of the CodeObject or None
        :return type: str|None
        """
        if code_obj_id in self.objects.keys() and hasattr(self.objects[code_obj_id], "docstring"):
            return self.objects[code_obj_id].docstring
        return None

    def get_code(self, code_obj_id: str)->str|None:
        """
        Get the code of a CodeObject, if exists
        
        :param code_obj_id: CodeObject id
        :type code_obj_id: str

        :return: code of the CodeObject or None
        :return type: str|None
        """
        if code_obj_id in self.objects.keys() and hasattr(self.objects[code_obj_id], "code"):
            return self.objects[code_obj_id].code
        return None

    def get_arguments(self, code_obj_id: str)->list[str]|None:
        """
        Get the arguments of a CodeObject, if exists. DO not return self as an argument
        
        :param code_obj_id: CodeObject id
        :type code_obj_id: str

        :return: arguments of the CodeObject or None
        :return type: list[str]|None
        """
        if code_obj_id in self.objects.keys() and hasattr(self.objects[code_obj_id], "arguments"):
            return [argument for argument in self.objects[code_obj_id].arguments if argument["name"] != "self"] # ignore self
        return None

    def get_return_type(self, code_obj_id: str)->str|None:
        """
        Get the return type of a CodeObject, if exists
        
        :param code_obj_id: CodeObject id
        :type code_obj_id: str

        :return: return type of the CodeObject or None
        :return type: str|None
        """
        if code_obj_id in self.objects.keys() and hasattr(self.objects[code_obj_id], "return_type"):
            return self.objects[code_obj_id].return_type
        return None

    def get_exceptions(self, code_obj_id: str)->list[str]|None:
        """
        Get the exceptions of a CodeObject, if exists
        
        :param code_obj_id: CodeObject id
        :type code_obj_id: str

        :return: exceptions raised by the CodeObject or None
        :return type: list[str]|None
        """
        if code_obj_id in self.objects.keys() and hasattr(self.objects[code_obj_id], "exceptions"):
            return self.objects[code_obj_id].exceptions
        return None

    def get_missing_arg_types(self, code_obj_id: str)->list[str]|bool:
        """
        Get the names of arguments where type information is missing of a CodeObject, if exists
        
        :param code_obj_id: CodeObject id
        :type code_obj_id: str

        :return: names of arguments where type information is missing or False
        :return type: list[str]|bool
        """
        code_obj = self.objects[code_obj_id]
        if not isinstance(code_obj, MethodObject):
            return False
        return code_obj.get_missing_arg_types()

    def return_type_missing(self, code_obj_id: str)->bool:
        """
        Return if the return type of the CodeObject is missing
        
        :param code_obj_id: CodeObject id
        :type code_obj_id: str
        
        :return: True if return type is missing, else False
        :return type: bool
        """
        code_obj = self.objects[code_obj_id]
        if not isinstance(code_obj, MethodObject):
            return False
        return code_obj.missing_return_type
    
    def get_args_types_exceptions(self, code_obj_id: str)->dict[str, list[str]|str|bool]:
        """
        Get information about arguments, return and exceptions of a CodeObject
        
        :param code_obj_id: id of the CodeObject
        :type code_obj_id: str
        
        :return: information about arguments, return and exceptions
        :return type: dict[str, list[str]|str|bool]
        """
        return {"arguments": self.get_arguments(code_obj_id=code_obj_id),
                "return_type": self.get_return_type(code_obj_id=code_obj_id),
                "exceptions": self.get_exceptions(code_obj_id=code_obj_id),
                "missing_arg_types": self.get_missing_arg_types(code_obj_id=code_obj_id),
                "return_type_missing": self.return_type_missing(code_obj_id=code_obj_id),
                }

    def get_by_filename(self, filename: str)->list[CodeObject]:
        """
        Get CodeObjects by filename
        
        :param filename: filename for which CodeObjects should be returned
        :type filename: str
        
        :return: list of matching CodeObjecs
        :return type: list[CodeObject]
        """
        if not filename.endswith(".py"):
            filename += ".py"
        matches = []
        for object in self.objects.values():
            if object.filename == filename:
                matches.append(object)
        return matches

    def get_context_docstrings(self, code_obj_id: str)->dict[str, str]:
        """
        Get the docstrings of context CodeObjects as a dict of CodeObject id to docstring
        
        :param code_obj_id: CodeObject id
        :type code_obj_id: str
        
        :return: dictionary of CodeObject to docstrings
        :return type: dict[str, str]
        """
        code_obj = self.get(code_obj_id)
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

    def depends_on_outdated_code(self, code_obj_id: str)->bool:
        """
        Return if the CodeObject depends on other CodeObjects. Relevant for the order of docstring generation
        
        :param code_obj_id: CodeObject id
        :type code_obj_id: str
        
        :return: True if the CodeObject depends on other CodeObjects
        :return type: bool"""
        code_obj = self.get(code_obj_id)
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
    
    def update_docstring(self, code_obj_id: str, new_docstring: str):
        """
        Update the docstring of a CodeObject
        
        :param code_obj_id: CodeObject id
        :type code_obj_id: str
        :param new_docstring: the new docstring
        :type new_docstring: str
        """
        code_obj = self.get(code_obj_id)
        code_obj.old_docstring = code_obj.docstring
        code_obj.docstring = new_docstring
        code_obj.is_updated = True
        code_obj.outdated = False