# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import importlib.machinery
import os
import sys
from unittest import mock

project_root = os.path.join(__file__, "../../..")
sys.path.insert(0, os.path.abspath(project_root))

# Python modules that don't get installed in the doc build environment due to heaviness, so they get mocked.
# Each mock needs a real ModuleSpec so that importlib.util.find_spec() doesn't raise ValueError.
MOCK_MODULES = [
    "mlflow",
    "mlflow.artifacts",
    "mlflow.entities",
    "fiftyone",
    "datasets",
    "tensorflow",
    "IPython",
]
for mod_name in MOCK_MODULES:
    spec = importlib.machinery.ModuleSpec(mod_name, None)
    pkg = mod_name.rsplit(".", 1)[0] if "." in mod_name else mod_name
    mod = mock.MagicMock(
        __spec__=spec, __name__=mod_name, __path__=[], __file__=None, __loader__=None, __package__=pkg,
    )
    sys.modules[mod_name] = mod
    parts = mod_name.split(".")
    if len(parts) > 1:
        parent = sys.modules.get(parts[0])
        if parent is not None:
            setattr(parent, parts[-1], mod)

project = "DagsHub Client"
copyright = "2026, DagsHub"
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
