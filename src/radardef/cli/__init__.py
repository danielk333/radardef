# This is needed so that the registration is performed
from . import convert_cli, download_cli, format_cli
# Then expose the main after registration
from .commands_cli import main
