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
        self.class_attributes = []
        self.class_methods = []
        if code is not None:
            self.identify_class_attributes_and_methods(code=code, filename=filename)
        super().__init__(name, filename, "class", body=body, ast_tree=ast_tree, docstring=docstring, code=code)

    def add_module(self, module_obj):
        self.module_obj = module_obj
    
    def add_class_attribute(self, class_attribute):
        self.class_attributes.append(class_attribute)
        # TODO use this

    def add_class_method(self, class_method_id):
        self.class_methods.append(class_method_id)
        # TODO use this

    def identify_class_attributes_and_methods(self, code, filename):
        for line in code.split('\n'):
            # identify class attributes
            if line.lstrip().startswith("self.") and '=' in line: # TODO could match lines like self.var == "xyz" which is undesired. Please Fix
                attribute = line.split('=')[0].lstrip().lstrip("self.").rstrip()
                self.add_class_attribute(attribute)
            # identify class methods
            elif line.lstrip().startswith("def ") and line.split('#')[0].rstrip().endswith(':'):
                method_name = line.lstrip().lstrip("def ").split('(')[0]
                class_method_id = filename + '_method_' + method_name
                self.add_class_method(class_method_id=class_method_id)

        raise NotImplementedError


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