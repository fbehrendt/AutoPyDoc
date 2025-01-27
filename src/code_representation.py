class Code_obj():
    def __init__(self, name, filename, code_type, body):
        self.name = name
        self.filename = filename
        self.type = code_type
        self.id = filename + "_" + code_type + "_" + name
        self.body = body
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

class Class_obj(Code_obj):
    def __init__(self, name, filename, code_type, signature, body, module_obj=None):
        self.signature = signature
        self.module_obj = module_obj
        super().__init__(name, filename, code_type, signature, body)

    def add_module(self, module_obj):
        self.module_obj = module_obj

class Method_obj(Code_obj):
    def __init__(self, name, filename, code_type, signature, body, class_obj=None, module_obj=None):
        self.class_obj = class_obj
        self.module_obj = module_obj
        super().__init__(name, filename, code_type, signature, body)

    def add_module(self, module_obj):
        self.module_obj = module_obj
    
    def add_class(self, class_obj):
        self.class_obj = class_obj