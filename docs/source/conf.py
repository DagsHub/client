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

sitemap_url_scheme = "{link}"
