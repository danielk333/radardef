import logging
import os
import shutil
import subprocess
import zipfile
from itertools import chain
from pathlib import Path
from typing import Any, Optional

import requests
from lxml import html
from tqdm import tqdm


def format_bytes(size: float) -> str:
    """Convert bytes to a human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0

    return ""


# Start
# DAY=20161021 mode=leo_bpark_2.5u_3P
# url
# https://portal.eiscat.se/schedule/tape2.cgi?exp=leo_bpark_2.5u_3P&date=20161021
# url to download page
# https://portal.eiscat.se/schedule/tape2.cgi?date=20161021&exp=leo_bpark_2.5u_3P&dl=1
# dl == download = true
# location-based download tar or zip format
# https://portal.eiscat.se/schedule/download.cgi?r=249696&r=249698&maxtar=4&filename=leo_bpark_2.5u_3P20161021&submit=Location-based&format=tar
# https://portal.eiscat.se/schedule/download.cgi?r=249696&r=249698&maxtar=4&filename=leo_bpark_2.5u_3P20161021&submit=Location-based&format=zip
# zip download link -- all
# https://rebus.eiscat.se:37009/249696;249698/leo_bpark_2.5u_3P20161021.zip


QUERY_URL = "https://portal.eiscat.se/schedule/tape2.cgi"
DOWNLOAD_URL = "https://rebus.eiscat.se:37009"


def get_download_nodes(
    day: str, mode: str, logger: Optional[logging.Logger] = None
) -> list[list[dict[str, Any]]] | None:
    """Extract node identifiers from download page"""
    url = f"{QUERY_URL}?exp={mode}&date={day}&dl=1"
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.text
        # parse
        tree = html.fromstring(html_content)
        checkboxes = tree.xpath('//input[@type="checkbox"]')
        trs = [cb.xpath("./ancestor::tr[1]") for cb in checkboxes]
        flattened_trs = list(chain.from_iterable(trs))
        product_nodes = []
        nodes = []
        for tr in flattened_trs:
            tds = tr.xpath(".//td")
            node = {}
            # tds[0]
            cb = tds[0].find('.//input[@name="r"]')
            node["id"] = cb.get("value")
            # tds[1]
            node["type"] = type = tds[1].text
            # tds[2]
            node["start"] = tds[2].text
            if type == "data":
                # tds[3]
                node["end"] = tds[3].text
                # tds[5]
                # NOTE: assuming number is given in KB
                node["bytes"] = int(tds[5].text) * 1024
            elif type == "info":
                # tds[4]
                tokens = tds[4].text.split(" ")
                node["exp"] = {"instrument": tokens[1], "mode": tokens[2]}
            nodes.append(node)
            if type == "info":
                product_nodes.append(nodes)
                nodes = []
        return product_nodes
    else:
        if logger:
            logger.error(f"Failed to fetch the HTML content. Status code: {response.status_code}")
        return None


def download(
    day: str,
    mode: str,
    instrument: str,
    dst: str,
    logger: Optional[logging.Logger] = None,
    progress: bool = False,
    wget: bool = False,
) -> str | None:
    """Download zip file with eiscat measurements.

    Example:

    ```python
        path = download('20220408','leo_bpark_2.1u_NO', 'uhf', '/data')
    ```

    This function uses a specific download link, for which data access is
    geo-restricted to IP-addresses in Scandinavia. The link also uses a
    non-standard port number, so it may be blocked by an agressive firewall. For
    data access outside Scandinavia, see https://eiscat.se/

    The triplet ('day', 'mode', 'instrument') must correspond to an actual
    dataset in the Eiscat archive. Search for available datasets is possible
    using the Web portal https://portal.eiscat.se/. If a download is interrupted
    by the user (ctrl-c), the incomplete zip download file will be removed.

    Args:
        day: Day of experiment ("YYYYMMDD")
        mode: Mode identifier
        instrument: Instrument identifier
        dst: Path to folder where downloaded zip file will be stored
        logger (optional): Optional logger object
        progress (optional): Print download progress bar to stdout
        wget (optional): Use wget instead of requests for download, default = False

    Returns:
        The absolute path to the downloaded zip file or None.

    Raises:
        FileNotFoundError: 'dst' does not exist
        ExceptioN:  target product does not exist

    """
    path = Path(dst)
    if not path.is_dir():
        raise FileNotFoundError(f"<dst> '{path}' is not a directory")

    # zip
    zip_filename = f"{mode}-{day}-{instrument}.zip"
    zip_download = path / zip_filename

    # check if downloaded zipfile already exists
    if zip_download.exists():
        if logger:
            logger.info(f"Zipfile exists: {zip_download}")
        zip_download = zip_download
        return str(zip_download)

    # Fetch download nodes
    product_nodes = get_download_nodes(day, mode, logger=logger)

    if (product_nodes == None) or (len(product_nodes) == 0):
        raise Exception("No product nodes")

    # select product
    data_nodes = []
    info_nodes = []
    for nodes in product_nodes:
        data_nodes = [node for node in nodes if node["type"] == "data"]
        info_nodes = [node for node in nodes if node["type"] == "info"]

        # check that data matches given instrument
        _instrument = info_nodes[0]["exp"]["instrument"]
        if instrument.casefold() != _instrument.casefold():
            # mismatch instrument
            continue
        else:
            # found first
            break

    if len(data_nodes) == 0:
        raise Exception("No data nodes for product", product_nodes)

    # Size
    bytes = sum([node["bytes"] for node in data_nodes])
    size = format_bytes(bytes)

    # Url
    node_ids = [node["id"] for node in nodes]
    zip_url = f"{DOWNLOAD_URL}/{';'.join(node_ids)}/{mode}{day}.zip"

    # Download
    if logger:
        logger.info(f"Product: {mode} {day} {size}")
        logger.info(f"Url: {zip_url}")

    completed = False
    code = None

    if wget:
        # WGET
        command = ["wget", zip_url, "-P", str(dst), "-O", zip_filename]
        if not progress:
            command.append("-q")
        try:
            result = subprocess.run(command)
            if result.returncode == 0:
                completed = True
            else:
                code = result.returncode
        except KeyboardInterrupt:
            pass

    else:
        # REQUESTS
        response = requests.get(zip_url, stream=True)
        if response.status_code == 200:
            file_size = int(response.headers.get("Content-Length", 0)) or bytes
            if logger:
                logger.info(f"Download: zipfile: {zip_download}")
            # Use tqdm to create a progress bar
            if progress:
                pbar = tqdm(
                    desc="Downloading Eiscat raw data",
                    total=file_size,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                )

            with open(zip_download, "wb") as file:
                try:
                    for data in response.iter_content(chunk_size=1024):
                        file.write(data)
                        if progress:
                            pbar.update(len(data))
                    completed = True
                    if logger:
                        logger.info("Download: completed")
                except KeyboardInterrupt:
                    pass
                if progress:
                    pbar.close()
        else:
            code = response.status_code

    if not completed:
        # cleanup
        os.remove(zip_download)
        if logger:
            if code is None:
                logger.warning("Download: terminiated")
            else:
                logger.info(f"Download: fail - status code: {code}")
        return None
    else:
        return str(zip_download)


def extract_zip(
    src: str, dst: str, cleanup: bool = True, logger: Optional[logging.Logger] = None
) -> tuple[bool, dict[str, list[str]] | str]:

    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.is_file():
        return False, f"Zipfile: missing {src_path}"

    if not dst_path.is_dir():
        return False, f"No dst directory {dst_path}"

    # make temporary extraction folder
    # extract_dir = dst / str(uuid.uuid4())
    # extract_dir.mkdir(exist_ok=True, parents=True)

    if logger:
        logger.info(f"Unzip: start {dst_path}")

    # Extract zip file to random location in dst directory
    with zipfile.ZipFile(src_path, "r") as zip_ref:
        paths = [Path(p) for p in zip_ref.namelist()]
        rootpaths = list(set([p.parts[0] for p in paths]))
        extract_dirs = [dst_path / p for p in rootpaths]
        # could check if extracted dirs already exist
        zip_ref.extractall(dst_path)

    if cleanup:
        os.remove(str(src_path))

    if logger:
        logger.info(f"Unzip: done {extract_dirs}")

    return True, {"paths": [str(p) for p in extract_dirs]}


def move_tree(
    src: str, dst: str, update: bool = False, logger: Optional[logging.Logger] = None
) -> tuple[bool, dict[str, str] | str]:
    src_path = Path(src)
    dst_path = Path(dst)
    if not dst_path.is_dir():
        return False, f"No <dst> directory {dst_path}"

    # move src to dst
    if update and dst_path.is_dir():
        # update
        # move subfolders of src individually - if not exists
        for src_subdir in src_path.iterdir():
            dst_subdir = dst_path / src_subdir.name
            if not dst_subdir.exists():
                shutil.move(str(src_subdir), str(dst_subdir))
    else:
        # move
        shutil.move(str(src_path), str(dst_path))

    return True, {"path": str(dst_path / src_path.name)}


"""
    if __name__ == '__main__':

    day = '20220408'
    mode = 'leo_bpark_2.1u_NO'
    instrument = 'uhf'
    # logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    def test_download_nodes():
        nodes = get_download_nodes(day, mode)
        import pprint
        pprint.pprint(nodes)

    def test_download():
        day = '20101125'
        mode = 'leo_sat_1.0l_EI'
        instrument = '42m'
        dst = "."
        wget = True
        ok, result = download(day, mode, instrument, dst,
      logger=logger, progress=True, wget=wget)
       print(ok, result)

       def test_extract():
       zip = "leo_bpark_2.1u_NO-20220408-uhf.zip"
       dst = "."
       ok, result = extract_zip(zip, dst, logger=logger)
       print(ok, result)

       def test_move():
       dst = "3a79f529-6a94-418d-b42e-cbc676036489"
       src = "dst"
       ok, result = move_tree(src, dst, logger=logger)
       print(ok, result)

       test_download()
       # test_extract()
        # test_move()
"""
