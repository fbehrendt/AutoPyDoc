class Code_obj():
    def __init__(self, name, filename, code_type, body, docstring=None, ast=None, code=None):
        self.name = name
        self.filename = filename
        self.type = code_type
        self.id = filename + "_" + self.type + "_" + self.name
        self.body = body
        if docstring:
            self.docstring = docstring
        if ast:
            self.ast=ast
        if code:
            self.code = code
        self.called_methods = {}
        self.called_classes = {}
        self.called_by_methods = {}
        self.called_by_classes = {}
        self.called_by_modules = {}
    
    def add_called_method(self, called_method):
        self.called_methods[called_method.id] = called_method
    
    def add_called_class(self, called_class):
        self.called_classes[called_class.id] = called_class

    def add_caller_method(self, caller_method):
        self.called_by_methods[caller_method.id] = caller_method
    
    def add_caller_class(self, caller_class):
        self.called_by_classes[caller_class.id] = caller_class
    
    def add_caller_module(self, caller_module):
        self.called_by_modules[caller_module.id] = caller_module

    def add_docstring(self, docstring):
        self.docstring = docstring
    
    def add_ast(self, ast):
        self.ast = ast
    
    def add_code(self, code):
        self.code = code

class Class_obj(Code_obj):
    def __init__(self, name, filename, signature, body, module_obj=None):
        self.signature = signature
        self.module_obj = module_obj
        super().__init__(name, filename, "class", signature, body)

    def add_module(self, module_obj):
        self.module_obj = module_obj

class Method_obj(Code_obj):
    def __init__(self, name, filename, signature, body, class_obj=None, module_obj=None):
        self.class_obj = class_obj
        self.module_obj = module_obj
        self.signature = signature
        super().__init__(name, filename, "method", body)

    def add_module(self, module_obj):
        self.module_obj = module_obj
    
    def add_class(self, class_obj):
        self.class_obj = class_obj

class CodeRepresenter():
    def __init__(self):
        self.objects = {}
    
    def add_code_obj(self, code_obj):
        if code_obj.id not in self.objects:
            self.objects[code_obj.id] = code_obj