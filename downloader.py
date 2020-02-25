import argparse
import os
import uuid
from functools import partial

import loguru

import youtube_dl


def init_logger():
    logger = loguru.logger

    return logger


def parse_args():
    parsers = argparse.ArgumentParser()

    parsers.add_argument(
        "--url",
        "-u",
        type=str,
        required=True,
        action="store",
        help="Playlist url"
    )
    parsers.add_argument(
        "--path",
        "-p",
        default="./download",
        type=str,
        required=False,
        action="store",
        help="Path for download folder"
    )
    parsers.add_argument(
        "--convert",
        "-c",
        default=False,
        type=str,
        required=False,
        action="store",
        help="Convert to mp3"
    )

    return parsers.parse_args()


class LoggerWrapperForYoutubeDl(object):
    def __init__(self, logger):
        self._logger = logger

    def debug(self, msg):
        self._logger.debug(msg)

    def warning(self, msg):
        self._logger.warning(msg)

    def error(self, msg):
        self._logger.error(msg)


def download_progress_hook(logger, detailed_status):
    logger.info("Status updated: {}".format(detailed_status))
    if detailed_status["status"] == "finished":
        logger.info("Done downloading, now converting...")


def download(logger, url, convert_to_mp3, download_folder):
    download_uuid = str(uuid.uuid4())
    logger.info("Downloading uuid: {}".format(download_uuid))

    logger_wrapper = LoggerWrapperForYoutubeDl(logger)
    download_folder = os.path.join(download_folder, download_uuid)
    os.makedirs(download_folder)

    download_path_template = download_folder + "/%(title)s.%(ext)s"
    logger.info("Download mask: {}".format(download_path_template))

    wrapped_download_progress_hook = partial(download_progress_hook, logger)
    ydl_opts = {
        "logger": logger_wrapper,
        "outtmpl": download_path_template,
        "progress_hooks": [wrapped_download_progress_hook],
        "ignoreerrors": True
    }

    if convert_to_mp3:
        ydl_opts["format"] = "bestaudio/best"

        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def main():
    logger = init_logger()
    logger.info("application started")

    logger.info("parsing command line arguments")
    args = parse_args()

    download_folder = args.path
    logger.debug("Download folder from config: {}".format(download_folder))

    if not os.path.exists(download_folder):
        logger.info("Folder for downloading doesn't exists, creating. Folder name: {}".format(download_folder))
        os.makedirs(download_folder)

    logger.info("Configuring handler for Ctrl-C")

    download(logger, args.url, args.convert, download_folder)


if __name__ == "__main__":
    main()
