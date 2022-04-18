import asyncio
import csv
from time import sleep
from rich.console import Console
import signal
import logging
import pathlib
import time


from datetime import datetime


from .utils.logging_utils import get_cur_logger_dir

import subprocess
from subprocess import DEVNULL

from src.sensor_services.sensing_service_manager import SensingServiceManager


# 10 samples a second
SAMPLE_RATE = 5


class DataLogger:

    def __init__(self, filename, all_keys):

        self.handle = open(filename, "a")
        self.dict_keys = ["time_ms", *all_keys]

        self.wrtr = csv.DictWriter(self.handle, self.dict_keys)
        self.wrtr.writeheader()  # write once

    def print(self, data):

        data["time_ms"] = time.time()

        # if self.handle.tell() == 0: always write header

        self.wrtr.writerow(data)
        self.handle.flush()

    def __del__(self):
        self.handle.close()

        del self.handle
        del self.wrtr


class SensingClient:

    _logger = None

    _loop = None

    last_data = None

    def __init__(self, service_manager: SensingServiceManager):

        # cop out, i know
        # time.sleep(15)

        self.console = Console()
        self.err_console = Console(stderr=True)
        # self.loop = asyncio.get_running_loop()

        self.service_manager = service_manager
        # self.service_manager.start_service("example_service")

        signal.signal(signal.SIGINT, self.sigint_handler)

        asyncio.run(self.run())

    def get_data_logger(self):

        keys = []
        for service in self.service_manager.registered_services.values():
            keys += list(service.service_class.get_keys())

        logfile_dir = "data/{}".format(
            datetime.now().strftime("%Y%m%d"))

        logfile = logfile_dir + \
            "/{}.csv".format(datetime.now().strftime("%H_%M"))

        return DataLogger(logfile, keys)

    async def run(self):

        print("Running")

        data_logger = self.get_data_logger()

        last_speak = None

        await self.service_manager.start()

        async for sensor_data in self.service_manager.monitor_services(sample_rate=SAMPLE_RATE):

            self.last_data = sensor_data

            data_logger.print(sensor_data)

            if last_speak is None or time.time() - last_speak > 30:
                self.speak()
                last_speak = time.time()

    def sigint_handler(self, _, _1):
        print("CTRL+C pushed")

        raise Exception()

    def get_logger(self):

        if self._logger is not None:
            return self._logger

        self._logger = logging.getLogger(type(self).__name__)

        if self._logger.handlers:
            return self._logger

        logfile_dir = get_cur_logger_dir()

        logfile = logfile_dir + "/general.log"

        self._logger.setLevel(logging.DEBUG)

        filehandler = logging.FileHandler(
            logfile
        )

        formatter = logging.Formatter(
            # [Process: %(process)d, %(filename)s:%(funcName)s(%(lineno)d)]
            "[%(asctime)s| %(processName)s> %(levelname)s] %(message)s"
        )

        filehandler.setFormatter(formatter)

        self._logger.addHandler(filehandler)

        return self._logger

    def speak(self):

        logger = self.get_logger()

        try:
            service_list = self.service_manager.get_healthy_services()

            service_ids = [service.service_id for service in service_list]

            if len(service_list) == 0:
                message = "No services healthy"
            else:
                message = "The following services are healthy and running: {}".format(
                    ",".join(service_ids))

                message += ";;"

                for service in service_list:

                    try:
                        if self.last_data is None or not isinstance(self.last_data, dict):
                            continue

                        message += service.service_id + " has " + \
                            service.service_class.speak_data(
                                self.last_data) + ". "
                    except Exception as e:

                        logger.critical("Failed to speak data {}".format(e))

            print(message)
            subprocess.Popen(["espeak", "\"{}\"".format(
                message)], stdout=DEVNULL, stderr=DEVNULL)
        except Exception as e:
            logger.critical("Failed to speak data {}".format(e))
