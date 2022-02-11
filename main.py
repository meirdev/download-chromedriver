"""
Download the latest ChromeDriver for Chrome.
See: https://sites.google.com/chromium.org/driver/downloads/version-selection

The chrome executable file is usually located in:
Linux:   /usr/bin/google-chrome
Windows: C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
Mac:     /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from xml.dom.minidom import parseString

import requests


STORAGE_URL = "https://chromedriver.storage.googleapis.com"


def get_chrome_version(chrome_executable: str) -> str:
    if sys.platform == "win32":
        command = f"powershell -command (Get-Item '{chrome_executable}').VersionInfo.ProductVersion"
    else:
        command = f"{chrome_executable} --version"
    return subprocess.check_output(command, shell=True, text=True)


def get_download_link(chrome_version: str, platform: str) -> str:
    version_match = re.search(r"(?P<version>\d+\.\d+\.\d+)\.\d+", chrome_version)
    if version_match is None:
        raise ValueError(f"Could not parse Chrome version: {chrome_version}")

    latest_release = requests.get(
        f"{STORAGE_URL}/LATEST_RELEASE_{version_match.group('version')}"
    )
    chrome_drivers = requests.get(
        f"{STORAGE_URL}/?delimiter=/&prefix={latest_release.text}/"
    )

    root = parseString(chrome_drivers.text)
    for key in root.getElementsByTagName("Key"):
        filename = key.childNodes[0].data
        if platform in filename:
            return f"{STORAGE_URL}/{filename}"

    raise ValueError(f"Could not find ChromeDriver for {platform}.")


def download_and_extract(url: str, dst: str) -> None:
    file = requests.get(url, allow_redirects=True)
    with tempfile.NamedTemporaryFile("wb") as fp:
        fp.write(file.content)
        fp.flush()

        # We need it for Windows, see: https://stackoverflow.com/a/15235559
        temp_opener = lambda name, flag, mode=0o777: os.open(
            name, flag | os.O_TEMPORARY, mode
        )

        with open(fp.name, "rb", opener=temp_opener) as zip_fp:
            with zipfile.ZipFile(zip_fp) as zip_file:
                zip_file.extractall(dst)


def get_arg_parser() -> argparse.ArgumentParser:
    arg_parser = argparse.ArgumentParser(
        description="Download the latest ChromeDriver for Chrome."
    )
    arg_parser.add_argument(
        "-e",
        "--chrome-executable",
        required=True,
        help="The path to the Chrome executable.",
    )
    arg_parser.add_argument(
        "-p",
        "--platform",
        default=sys.platform,
        help="The platform to download the ChromeDriver for.",
    )
    arg_parser.add_argument(
        "-o",
        "--output",
        default=os.getcwd(),
        help="The path to the output file.",
    )
    return arg_parser


def main() -> None:
    arg_parser = get_arg_parser()
    args = arg_parser.parse_args()

    chrome_version = get_chrome_version(args.chrome_executable)
    url = get_download_link(chrome_version, args.platform)
    download_and_extract(url, args.output)


if __name__ == "__main__":
    main()
