class Code_obj():
    def __init__(self, name, filename, code_type, body, ast_tree, docstring=None, code=None):
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
        self.called_methods = []
        self.called_classes = []
        self.called_by_methods = []
        self.called_by_classes = []
        self.called_by_modules = []
    
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

class Class_obj(Code_obj):
    def __init__(self, name, filename, signature, body, ast_tree, class_obj_id=None, module_obj_id=None, docstring=None, code=None):
        self.signature = signature
        self.class_obj_id = class_obj_id
        self.module_obj_id = module_obj_id
        super().__init__(name, filename, "class", body=body, ast_tree=ast_tree, docstring=docstring, code=code)

    def add_module(self, module_obj):
        self.module_obj = module_obj

class Method_obj(Code_obj):
    def __init__(self, name, filename, signature, body, ast_tree, class_obj_id=None, module_obj_id=None, docstring=None, code=None):
        self.signature = signature
        self.class_obj_id = class_obj_id
        self.module_obj_id = module_obj_id
        super().__init__(name, filename, "method", body, ast_tree, docstring=docstring, code=code)

    def add_module(self, module_obj_id):
        self.module_obj_id = module_obj_id
    
    def add_class(self, class_obj):
        self.class_obj = class_obj

class CodeRepresenter():
    def __init__(self):
        self.objects = {}
    
    def add_code_obj(self, code_obj):
        if code_obj.id not in self.objects:
            self.objects[code_obj.id] = code_obj