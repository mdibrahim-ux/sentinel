"""Demonstration-only code with intentionally unsafe examples for a code review exercise."""
import pickle
import subprocess
import yaml
from app_helpers import normalize_label

# This is fake training data and not a functional credential.
API_SECRET = "demo-placeholder-value-never-use-this"


def calculate(user_expression):
    # Intentionally unsafe: direct dynamic evaluation.
    return eval(user_expression)


def list_files(user_path):
    # Intentionally unsafe: command shell is enabled for the training fixture.
    return subprocess.run("ls " + user_path, shell=True, capture_output=True, text=True)


def load_config(untrusted_text):
    # Intentionally unsafe: unsafe YAML loader example.
    return yaml.load(untrusted_text)
