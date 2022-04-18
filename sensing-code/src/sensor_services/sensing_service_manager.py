
import asyncio
from multiprocessing import Pipe
from typing import Dict, List

from .service_delegate import ServiceDelegate


import logging

from ..utils.logging_utils import get_cur_logger_dir
import time


class SensingServiceManager:

    registered_services: Dict[str, ServiceDelegate] = {}

    _logger = None

    def __init__(self, services):
        self._register_services(services)

    def _register_services(self, services):
        """
        Takes list of services and adds them to the list.
        It additionally ensures there is a delegate for each service type.
        """
        self.registered_services = self._ensure_services(services)

    def _ensure_services(self, services):
        """
        Internal Function
        Takes in a list of services then:

        - ensure service is not already registered
        - creates a service delegate for the service

        Returns list as dictionary from {[id]: service_delegate}
        """
        service_dict = {}

        for service in services:
            if service.__id__ in service_dict or self.registered_services.get(service.__id__) is not None:
                raise Exception(
                    "Service {} already registered", service.__id__)

            service_dict[service.__id__] = ServiceDelegate(
                service.__id__, service, self.get_logger())

        return service_dict

    def configure_service(self, service_id, config):
        """
        Provide configuration value to services. Should only be done
        before a service is started.
        """

        service_status = self.get_service_status(service_id)

        if service_status.is_running:
            raise Exception(
                "Service {} is already running".format(service_id))

        service_status.config = config

    async def start(self):

        for service_id in self.registered_services.keys():
            await self.start_service(service_id)

    def get_service_status(self, service_id) -> ServiceDelegate:
        if service_id not in self.registered_services:
            raise Exception(
                "Service {} not a registered service".format(service_id))

        return self.registered_services[service_id]

    def get_active_services(self):

        return [service_id for service_id, service_status in self.registered_services.items() if service_status.is_running]

    async def start_service(self, service_id):
        return await self.registered_services[service_id].start(is_manual=True)

    async def get_all_data(self, data_timeout):
        # logger = self.get_logger()
        data_obj = {}

        coros = []
        for service_id in self.get_active_services():
            coros.append(self.registered_services[service_id].get_data(
                data_timeout=data_timeout))

        gathered = await asyncio.gather(*coros)

        for data in gathered:
            if data is not None and isinstance(data, dict):
                data_obj.update(data)

        return data_obj

    def terminate_service(self, service_id):

        logger = self.get_logger()

        service_status = self.get_service_status(service_id)

        if not service_status.is_running:
            logger.info(
                "Tried to terminate service {} but service not started.".format(service_id))
            return False

        service_status.terminate_handle()

    def get_logger(self):

        if self._logger is not None:
            return self._logger

        self._logger = logging.getLogger(type(self).__name__)

        if self._logger.handlers:
            return self._logger

        logfile_dir = get_cur_logger_dir()

        logfile = logfile_dir + "/service_manager.log"

        self._logger.setLevel(logging.DEBUG)

        filehandler = logging.FileHandler(
            logfile
        )

        formatter = logging.Formatter(
            # [Process: %(process)d, %(filename)s:%(funcName)s(%(lineno)d)]
            "[%(asctime)s| %(processName)s> %(levelname)s] %(message)s"
        )

        filehandler.setFormatter(formatter)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)

        self._logger.addHandler(filehandler)
        self._logger.addHandler(ch)

        return self._logger

    async def tlc_services(self):
        """ Provice TLC to services

            This means:
            - Restarting services which refuse to start up to 5 times at exponential backoff
            - Restarting services which are unhealthy (not responding to heartbeat)

        """

        for service_id, service_status in self.registered_services.items():
            if service_status.should_reboot and not service_status.is_healthy and not service_status.is_waiting_to_reboot:
                service_status.stop()
                await service_status.try_reboot()

    def get_healthy_services(self) -> List[ServiceDelegate]:

        services: List[ServiceDelegate] = []
        for service, delegate in self.registered_services.items():
            if self.registered_services[service].is_healthy:
                services.append(delegate)
        return services

    async def monitor_services(self, sample_rate):
        """
        Monitor services, yielding data at the given sample rate.

        Additionally perform tlc on services (including restarting iff sick.)
        """
        sampling_timeout = 1/sample_rate

        last_reading_time = time.time()

        loop = asyncio.get_event_loop()
        while True:

            d = await self.get_all_data(data_timeout=sampling_timeout)

            yield d

            loop.create_task(self.tlc_services())

            # sleep the required time to keep the same sample rate
            loop_time = time.time() - last_reading_time

            await asyncio.sleep(max(sampling_timeout - loop_time, sampling_timeout))

            self.get_logger().debug("Sampling rate: {}".format(
                1/(time.time() - last_reading_time) if time.time() - last_reading_time > 0 else 0))

            last_reading_time = time.time()
