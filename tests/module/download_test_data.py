import urllib.request
from pathlib import Path
from zipfile import ZipFile


def download_test_data(path: Path):

    if path.is_dir() is False:
        downloaded_zip_location = path.with_name(f"{path.name}.zip").resolve()
        if not downloaded_zip_location.is_file():
            url = "https://cloud.irf.se/public.php/dav/files/E4agksbcDx5zgDe/?accept=zip"
            urllib.request.urlretrieve(url, downloaded_zip_location)

        with ZipFile(downloaded_zip_location, "r") as zObject:
            zObject.extractall(path=path.parent)

        downloaded_zip_location.unlink()
