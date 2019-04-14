import ast
import importlib
import logging
import os
import pprint
import sys

from .analyzer import Analyzer


console = logging.StreamHandler()
console.setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
logger.addHandler(console)

seen_modules = set()

DO_NOT_DELETE = {
    "latin_1.py",
    "utf_8.py",
    "site.py",
    "_sitebuiltins.py",
    "sysconfig.py",
    "_sysconfigdata_m_linux_x86_64-linux-gnu.py",
}


def _warn(module, package_name):
    if package_name:
        logger.warn("Module not found: %s.%s", package_name, module.path)
    else:
        logger.warn("Module not found: %s", module.path)


def _import_module(module, package_name=None):
    try:
        return importlib.import_module(module.path, package=package_name)
    except ModuleNotFoundError:
        # The last part might not be a module.
        module_path = ".".join(module.path.split(".")[:-1])
        if not module_path:
            _warn(module, package_name)
            return
        try:
            return importlib.import_module(module_path, package=package_name)
        except ModuleNotFoundError:
            _warn(module, package_name)
        except ImportError as e:
            logger.error(e)
    except ImportError as e:
        logger.error(e)


def recurse_modules(modules):
    for imported_module in modules:
        if not hasattr(imported_module, "__file__"):
            logger.warning("%s has no __file__", imported_module.__name__)
            continue

        logger.info(imported_module.__file__)
        if imported_module.__file__ not in seen_modules:
            with open(imported_module.__file__, "r") as f:
                try:
                    tree = ast.parse(f.read())
                except UnicodeDecodeError:
                    # Probably a binary file, so just add it.
                    seen_modules.add(os.path.realpath(f.name))
                    continue

            seen_modules.add(imported_module.__file__)
            analyzer = Analyzer()
            analyzer.visit(tree)
            imports = []
            for module in analyzer.imports:
                if module.path.startswith("."):
                    try:
                        package_name = imported_module.__name__
                    except AttributeError:
                        logger.error("Cannot get name for %s, %s, %s", module, module.name, module.level)
                        continue
                    package_name = ".".join(package_name.split(".")[:module.level])
                    m = _import_module(module, package_name)
                    if m:
                        imports.append(m)
                else:
                    m = _import_module(module)
                    if m:
                        imports.append(m)
            recurse_modules(imports)


def purge(modules_to_keep):
    for path in sys.path:
        if path.endswith(".zip"):
            continue
        if path == '':
            # This is the local dir.
            path = '.'

        for directory in os.walk(path):
            for filename in directory[2]:
                full_path = os.path.join(directory[0], filename)
                if full_path not in modules_to_keep:
                    if filename in DO_NOT_DELETE:
                        continue

                    print(f"Deleting {full_path}")
                    os.unlink(full_path)


def shake(entry_point):
    with open(entry_point, "r") as infile:
        tree = ast.parse(infile.read())
        seen_modules.add(os.path.realpath(infile.name))

    analyzer = Analyzer()
    analyzer.visit(tree)
    modules = [_import_module(module) for module in analyzer.imports]
    recurse_modules(modules)
    pprint.pprint(seen_modules)
    purge(seen_modules)
