import ast

class ImportFinder():
    def __init__(self, filename=None):
        self.import_lines = {}
        self.imports = {}
        if filename is not None:
            self.add_file(filename=filename)
    
    def add_file(self, filename):
        current_file_imports = []
        for node in ast.walk(ast.parse(open(file=filename, mode='r').read())):
            if isinstance(node, ast.Import):
                for item in node.names:
                    current_file_imports.append(item.name)
            elif isinstance(node, ast.ImportFrom):          
                module = node.module
                for item in node.names:
                    current_file_imports.append(module + '.' + item.name)
        self.imports[filename] = current_file_imports

    def resolve_external_call(self, call, filename):
        # TODO does ast resolve external calls as module.method, or as method with module stored separately?
        # TODO resolve calls like class_obj_variable.class_method_call => get type of class_obj_variable
        # TODO resolve calls like self.class_obj.method, where class_obj was imported
        relevant_imports = self.imports[filename]
        matches = [current_import for current_import in relevant_imports if call.split('.')[0] in current_import]
        return matches
        

if __name__ == "__main__":
    filename = "src/repo_controller.py"
    import_finder = ImportFinder(filename=filename)
    print("Imports:")
    for import_line in import_finder.imports[filename]:
        print(import_line)
    matching_imports = import_finder.resolve_external_call(filename=filename, call="CodeParser")
    print("Call CodeParser found in", matching_imports)
    matching_imports = import_finder.resolve_external_call(filename=filename, call="CodeRepresenter")
    print("Call CodeRepresenter found in", matching_imports)
    matching_imports = import_finder.resolve_external_call(filename=filename, call="CodeParser.create_dependencies")
    print("Call CodeParser.create_dependencies found in", matching_imports)
    
    