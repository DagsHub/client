# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

project_root = os.path.join(__file__, "../../..")
sys.path.insert(0, os.path.abspath(project_root))

project = "DagsHub Client"
copyright = "2023, DagsHub"
author = "DagsHub"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx_copybutton",
    "sphinx_sitemap",
    "sphinx_click",
    "sphinx_autodoc_typehints",
]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_title = "DagsHub Client Docs"
html_baseurl = "https://dagshub.com/docs/client/"

html_theme_options = {
    "light_css_variables": {
        "color-problematic": "#4453B3",  # API names
        "color-background-secondary": "#f5f5f5",  # Sidebar BG
        "color-brand-content": "#00bda4",  # Links and active items
        "color-brand-primary": "#00bda4",  # ditto
        "color-sidebar-link-text--top-level": "rgba(0, 0, 0, 0.87)",  # Sidebar links
    },
    "dark_css_variables": {
        "color-problematic": "#C4B5FD",  # API names
        "color-background-primary": "hsl(189, 55%, 9%)",  # Main BG
        "color-background-secondary": "hsla(189, 55%, 5%, 1)",  # Sidebar BG
        "color-brand-content": "#00bda4",  # Links and active items
        "color-brand-primary": "#00bda4",  # ditto
        "color-sidebar-link-text--top-level": "rgba(226, 228, 233, 0.82)",  # Sidebar links
    },
}

html_js_files = [
    "js/gtm.js",
]

napoleon_include_init_with_doc = True
autodoc_member_order = "bysource"
autodoc_default_flags = ["inherited-members"]
autodoc_mock_imports = [
    "fiftyone",
    "mlflow",
    "datasets",
    "ultralytics",
    "cloudpickle",
    "hypercorn",
    "ngrok",
    "tensorflow",
    "IPython",
]
typehints_use_signature_return = True

sitemap_url_scheme = "{link}"


# -- Custom event handler for llms.txt and .md generation ---------------------
import os
from bs4 import BeautifulSoup
from markdownify import markdownify as md

def generate_llms_files(app, exc):
    if exc is None and app.builder.format == 'html':
        gendir = app.outdir
        print(f"Generating .md files and llms.txt in {gendir}...")

        llms_entries = []

        for root, dirs, files in os.walk(gendir):
            for file in files:
                if file.endswith(".html"):
                    html_path = os.path.join(root, file)
                    md_path = html_path[:-5] + ".md"

                    # Generate .md file
                    try:
                        with open(html_path, 'r', encoding='utf-8') as f:
                            html_content = f.read()

                        # Extract title for llms.txt
                        soup = BeautifulSoup(html_content, 'html.parser')
                        title_tag = soup.find('title')
                        page_title = title_tag.string.replace(" — DagsHub Client Docs", "").strip() if title_tag else file[:-5]

                        # Convert main content to Markdown
                        # Try to select a more specific content area if possible
                        # For Furo theme, 'main' role content or similar might be appropriate
                        main_content = soup.find('main') or soup.find(role='main') or soup.body
                        if main_content:
                             # Remove nav, header, footer, script, style if they are part of main_content
                            for unwanted_tag in main_content.find_all(['nav', 'header', 'footer', 'script', 'style', 'aside']):
                                unwanted_tag.decompose()
                            markdown_content = md(str(main_content), heading_style='atx')
                        else:
                            markdown_content = md(html_content, heading_style='atx')

                        with open(md_path, 'w', encoding='utf-8') as f:
                            f.write(markdown_content)
                        # print(f"Generated {md_path}")

                        # Add entry for llms.txt
                        # Create relative path from gendir for the URL
                        relative_md_path = os.path.relpath(md_path, gendir)
                        # Ensure forward slashes for URLs
                        llms_url = relative_md_path.replace(os.sep, '/')
                        llms_entries.append(f"- [{page_title}]({llms_url})")

                    except Exception as e:
                        print(f"Error processing {html_path}: {e}")

        # Generate llms.txt
        llms_txt_path = os.path.join(gendir, "llms.txt")
        project_title = app.config.project
        # Use a more generic description or make it configurable
        project_description = "Client library for DagsHub, providing tools to interact with DagsHub repositories and data."

        llms_content = f"# {project_title}\n\n"
        llms_content += f"> {project_description}\n\n"
        llms_content += "## Docs\n\n"
        llms_content += "\n".join(sorted(list(set(llms_entries)))) # Sort and remove duplicates

        try:
            with open(llms_txt_path, 'w', encoding='utf-8') as f:
                f.write(llms_content)
            print(f"Generated {llms_txt_path}")
        except Exception as e:
            print(f"Error generating {llms_txt_path}: {e}")

def setup(app):
    app.connect('build-finished', generate_llms_files)
