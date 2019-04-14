import ast


class Import:
    def __init__(self, name):
        self.name = name


class ImportFrom:
    def __init__(self, name, level):
        self.name = name
        self.level = level


class Analyzer(ast.NodeVisitor):
    def __init__(self):
        self.imports = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.imports.append(f"{'.' * node.level}{node.module}.{alias.name}")
        self.generic_visit(node)

    def visit_Call(self, node):
        if hasattr(node.func, "value") and hasattr(node.func.value, "id"):
            if node.func.value.id == "importlib":
                if node.func.attr == "__import__":
                    for arg in node.args:
                        try:
                            self.imports.append(arg.s)
                        except AttributeError as e:
                            print(e)
                if node.func.attr == "import_module":
                    for arg in node.args:
                        try:
                            self.imports.append(arg.s)
                        except AttributeError as e:
                            print(e)
        if getattr(node.func, "id", "") == "__import__":
            for arg in node.args:
                try:
                    self.imports.append(arg.s)
                except AttributeError as e:
                    print(e)
