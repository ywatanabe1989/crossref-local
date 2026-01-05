import os

def list_citation_styles(styles_directory: str) -> list:
    """
    List all citation styles available in the given directory.

    Args:
    - styles_directory: The path to the directory containing CSL style files.

    Returns:
    - A list of the names of the available citation styles.
    """
    # List all files in the given directory
    try:
        style_files = os.listdir(styles_directory)
        # Filter out files that are not CSL files
        csl_styles = [file for file in style_files if file.endswith('.csl')]
        # Extract the style names without the '.csl' extension
        style_names = [os.path.splitext(style)[0] for style in csl_styles]
        return style_names
    except Exception as e:
        print(f"Error accessing directory: {e}")
        return []

def list_citation_locales(locales_directory: str) -> list:
    """
    List all citation locales available in the given directory.

    Args:
    - locales_directory: The path to the directory containing CSL locale files.

    Returns:
    - A list of the names of the available citation locales.
    """
    # List all files in the given directory
    try:
        locale_files = os.listdir(locales_directory)
        # Filter out files that are not CSL files
        csl_locales = [file for file in locale_files if file.endswith('.xml')]
        # Extract the locale names without the '.xml' extension
        locale_names = [os.path.splitext(locale)[0].replace("locales-","") for locale in csl_locales]
        return locale_names
    except Exception as e:
        print(f"Error accessing directory: {e}")
        return []   

