class ImportFinder():
    def __init__(self, filename=None):
        self.import_lines = {}
        self.imports = {}
        if filename is not None:
            self.add_file(filename=filename)
    
    def add_file(self, filename):
        # TODO handle imports that include .py
        current_file_import_lines = []
        current_file_imports = []
        with open(filename, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if " import " in line:
                    current_file_import_lines.append(line.rstrip('\n'))
        self.import_lines[filename] = current_file_import_lines
        
        for line in current_file_import_lines:
            line = line.split('#')[0]
            line = line.strip()
            if "from " in line:
                line = line.lstrip("from ")
                module, imports_in_line = line.split(" import ")
                imports_in_line = imports_in_line.split(', ')
                for single_import in imports_in_line:
                    current_file_imports.append(module + '.' + single_import)
            else:
                line = line.lstrip("import ")
                imports_in_line = line.split(', ')
                for single_import in imports_in_line:
                    current_file_imports.append(single_import)
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
    print("Import lines")
    for import_line in import_finder.import_lines[filename]:
        print(import_line)
    print("Imports:")
    for import_line in import_finder.imports[filename]:
        print(import_line)
    matching_imports = import_finder.resolve_external_call(filename=filename, call="CodeParser")
    print("Call CodeParser found in", matching_imports)
    matching_imports = import_finder.resolve_external_call(filename=filename, call="CodeRepresenter")
    print("Call CodeRepresenter found in", matching_imports)
    matching_imports = import_finder.resolve_external_call(filename=filename, call="CodeParser.create_dependencies")
    print("Call CodeParser.create_dependencies found in", matching_imports)
    
    