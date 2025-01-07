import yaml


class ConfigurationError(Exception):
    """Base exception for SecurityAssistant-specific errors"""

    pass


def load_config(file_path):
    try:
        with open(file_path, "r") as file:
            config = yaml.safe_load(file)
        return config
    except (FileNotFoundError, yaml.YAMLError) as e:
        raise ConfigurationError(f"Error loading configuration file: {str(e)}")
