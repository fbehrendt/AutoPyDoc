class ImportFinder():
    def __init__(self, filename):
        self.import_lines = []
        with open(filename, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if " import " in line:
                    self.import_lines.append(line.rstrip('\n'))
        
        self.imports = []
        for line in self.import_lines:
            line = line.split('#')[0]
            line = line.strip()
            if "from " in line:
                line = line.lstrip("from ")
                module, imports = line.split(" import ")
                imports = imports.split(', ')
                for single_import in imports:
                    self.imports.append(module + '.' + single_import)
            else:
                line = line.lstrip("import ")
                imports = line.split(', ')
                for single_import in imports:
                    self.imports.append(single_import)

if __name__ == "__main__":
    import_finder = ImportFinder("src/repo_controller.py")
    print("Import lines")
    for import_line in import_finder.import_lines:
        print(import_line)
    print("Imports:")
    for import_line in import_finder.imports:
        print(import_line)
    