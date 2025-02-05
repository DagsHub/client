import pydoc
import pkgutil
import importlib
import sys

def generate_docs(package_name):
    package = importlib.import_module(package_name)
    print(f"\n# pydoc documentation for package: {package_name}\n")
    print("\n---\n")
    
    for _, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        print(f"\n## pydoc of module: {module_name}\n")
        print("\n---\n")
        
        try:
            docstring = pydoc.plain(pydoc.render_doc(module_name))
            print(docstring)
        except Exception as e:
            print(f"Error documenting {module_name}: {e}\n")
        
        print("\n---\n")
        print(f"\nEnd of documentation for module: {module_name}\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python gen-pydoc.py <package_name>")
        sys.exit(1)
    
    package_name = sys.argv[1]
    generate_docs(package_name)
