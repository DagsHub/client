import pydoc
import pkgutil
import importlib
import sys
import click


def generate_docs(package_name, output_file=None, file_prefix=None):
    package = importlib.import_module(package_name)

    out_f = open(output_file, 'w') if output_file else sys.stdout

    out_f.write(f"\n# pydoc documentation for package: {package_name}\n")
    out_f.write("\n---\n")

    for _, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        out_f.write(f"\n## pydoc of module: {module_name}\n")
        out_f.write("\n---\n")

        try:
            docstring = pydoc.plain(pydoc.render_doc(module_name))
            out_f.write(docstring)
        except Exception as e:
            out_f.write(f"Error documenting {module_name}: {e}\n")

        out_f.write("\n---\n")
        out_f.write(f"\nEnd of documentation for module: {module_name}\n")

        if file_prefix:
            module_filename = f"{file_prefix}_{module_name.replace('.', '_')}.txt"
            with open(module_filename, 'w') as module_file:
                module_file.write(docstring)

    if output_file:
        out_f.close()


@click.command()
@click.argument("package_name")
@click.option("--output-file", "-o", default=None, help="File to write full documentation output.")
@click.option("--file-prefix", "-p", default=None, help="Prefix for separate module documentation files.")
def main(package_name, output_file, file_prefix):
    generate_docs(package_name, output_file, file_prefix)


if __name__ == "__main__":
    main()
