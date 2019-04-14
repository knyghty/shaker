import ast
import logging


console = logging.StreamHandler()
console.setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
logger.addHandler(console)


class BaseImport:
    def __str__(self):
        return self.path


class DunderImport(BaseImport):
    def __init__(self, name):
        self.name = name
        self.path = name


class Import(BaseImport):
    def __init__(self, name):
        self.name = name
        self.path = name


class ImportFrom(BaseImport):
    def __init__(self, module, name, level):
        self.module = module
        self.name = name
        self.level = level
        self.path = f"{'.' * level}{module + '.' if module else ''}{name}"


class ImportModule(BaseImport):
    def __init__(self, name):
        self.name = name
        self.path = name


class Analyzer(ast.NodeVisitor):
    def __init__(self):
        self.imports = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(Import(alias.name))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.imports.append(ImportFrom(node.module, alias.name, node.level))
        self.generic_visit(node)

    def visit_Call(self, node):
        if hasattr(node.func, "value") and hasattr(node.func.value, "id"):
            if node.func.value.id == "importlib":
                if node.func.attr == "__import__":
                    self.parse_dunder(node)
                if node.func.attr == "import_module":
                    for arg in node.args:
                        try:
                            self.imports.append(ImportModule(arg.s))
                        except AttributeError as e:
                            logger.error(e)
        if getattr(node.func, "id", "") == "__import__":
            self.parse_dunder(node)

    def parse_dunder(self, node):
        try:
            path = node.args[0].s
        except AttributeError as e:
            logger.error(e)
        else:
            for keyword in node.keywords:
                if keyword.arg == "fromlist":
                    for from_import in getattr(keyword.value, "elts", []):
                        self.imports.append(DunderImport(path + "." + from_import.s))
