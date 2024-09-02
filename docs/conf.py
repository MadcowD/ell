# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ell'
copyright = '2024, William Guss'
author = 'William Guss'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Correct the extension name
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon', 'sphinxawesome_theme']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = "sphinxawesome_theme"

# Configure syntax highlighting for Awesome Sphinx Theme
pygments_style = "friendly"
pygments_style_dark = "monokai"

# Additional theme configuration
html_theme_options = {
    "show_prev_next": True,
    "show_scrolltop": True,
    "extra_header_links": {
        "API Reference": "reference/index",
        "Discord": "https://discord.gg/vWntgU52Xb",
    },

    "logo_light": "_static/ell-wide-light.png",
    "logo_dark": "_static/ell-wide-dark.png",
}



templates_path = ['_templates']