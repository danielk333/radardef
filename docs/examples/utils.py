import urllib.request
from pathlib import Path


def download_test_data(path: Path) -> Path:

    download_location = path / "MUI.000000.000000"
    if not download_location.is_file():
        url = "https://cloud.irf.se/public.php/dav/files/pXR6iYARobLxd2f/?accept=zip"
        urllib.request.urlretrieve(url, download_location)

    return download_location


def print_dir_items(dirs: list[Path]) -> None:
    for dir in dirs:
        print(f"{dir}")
        for file in dir.iterdir():
            print(f"├── {file.name}")
