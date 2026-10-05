import yaml


def load_config(text: str):
    return yaml.load(text)


def load_documents(text: str) -> list:
    return list(yaml.load_all(text))
