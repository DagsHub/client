# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "DagsHub client"
copyright = "2023, DagsHub"
author = "DagsHub"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
# html_logo = "dagshub.svg"
html_theme_options = {
    "light_logo": "light_logo.svg",
    "dark_logo": "dark_logo.svg",
    "sidebar_hide_name": True,
}

napoleon_include_init_with_doc = True
autodoc_member_order = 'bysource'
autodoc_default_flags = ["inherited-members"]
