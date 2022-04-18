
import asyncio
from multiprocessing import Pipe
from src.sensor_services.helpers import SERVICE_STATUS, SensingServiceHandle, ServiceError
from src.sensor_services.sensing_service import SensingService

from datetime import datetime, timedelta
from collections import deque

from src.utils.status_utils import STATUS_MESSAGES

HEARTBEAT_TIMEOUT = 1

REBOOT_LOOKUP_TIMEOUTS = [1, 10, 20, 50, 150]  # in seconds


class HEALTH_STATUS:
    OK = 0
    UNHEALTHY_WITH_SUCCESS = 1
    DEAD = 2


class ServiceDelegate:

    active_handle = None

    def __init__(self, service_id, service_class, logger, /, status=SERVICE_STATUS.STOPPED, errors=None, should_reboot=None, last_reboot=None, reboot_attempts=0) -> None:

        if not issubclass(service_class, SensingService):
            raise TypeError(
                "Service {}, is not a SensingService", type(service_class).__name__)
        if not hasattr(service_class, "__id__"):
            raise TypeError("Service {}, has no id attribute",
                            type(service_class).__name__)

        self.service_class = service_class
        self.service_id = service_id

        self.logger = logger
        self.status = status
        self.errors = [] if errors is None else errors
        self.should_reboot = should_reboot
        self.last_reboot = last_reboot
        self.reboot_attempts = reboot_attempts
        self.config = None

        self.active_handle = None
        self.last_error = None

        self._metric_events = deque(maxlen=1000)

    @property
    def is_running(self):
        return self.status == SERVICE_STATUS.RUNNING

    @property
    def is_waiting_to_reboot(self):
        return self.status == SERVICE_STATUS.WAITING_TO_REBOOT

    def terminate_handle(self):

        # fail silently if the handle is not running
        if self.active_handle is None:
            return

        del self.active_handle

    @property
    def is_healthy(self):
        # Return

        if self.status == SERVICE_STATUS.STOPPED_ILL:
            return False

        if len(self._metric_events) > 200 and self._metric_events.count(True) / len(self._metric_events) < 0.1:
            return False

        return True

    async def _spin_for_response(self, timeout, sleep_increment=0.1):
        start_time = datetime.now()
        while True:
            if (datetime.now() - start_time).total_seconds() > timeout:
                self.logger.debug(
                    "Service {} did not respond to heartbeat in time".format(self.service_id))
                raise TimeoutError(
                    "Service {} did not respond to heartbeat in time".format(self.service_id))

            if self.active_handle.recv_pipe.poll():
                break

            await asyncio.sleep(sleep_increment)

    async def get_data(self, data_timeout=0.5):
        """
        Get data from a service
        :param service_id: The id of the service to get data from.
        :param data_timeout: The timeout to wait for data.
        """

        logger = self.logger

        try:

            if self.active_handle is None:
                raise ServiceError(
                    "Service {} is not running".format(self.service_id))

            send_pipe = self.active_handle.send_pipe
            recv_pipe = self.active_handle.recv_pipe

            send_pipe.send((
                STATUS_MESSAGES.GET_DATA.value,
            ))

            logger.debug("Sent get data to service {}".format(self.service_id))

            await self._spin_for_response(data_timeout, sleep_increment=data_timeout/10)

            response = recv_pipe.recv()

            logger.debug(
                "Received data from service {}".format(self.service_id))

            if not isinstance(response, tuple) or len(response) != 2:

                raise ServiceError(
                    "Service {} did not respond with a tuple of (status, data)".format(self.service_id), critical=True)

            status_message_type, status_message_data = response

            if status_message_type == STATUS_MESSAGES.DATA_ERROR.value:
                err = None
                if len(response) == 2:
                    err = response[1]

                raise ServiceError(
                    "Service {} returned an error: {}".format(self.service_id, err))

            if status_message_type != STATUS_MESSAGES.DATA_OK.value:

                raise ServiceError(
                    "Service {} did not return a valid response".format(self.service_id))

            self._report_event(True)
            return status_message_data

        except Exception as e:
            logger.debug("Error during get_data in {}: {}".format(
                self.service_id, e))

            self.handle_error(e)

            return False

    async def check_heartbeat(self):
        logger = self.logger

        try:
            send_pipe = self.active_handle.send_pipe
            recv_pipe = self.active_handle.recv_pipe
            send_pipe.send(
                (STATUS_MESSAGES.HEARTBEAT_SYN.value, None))

            logger.debug(
                "Sent heartbeat to service {}".format(self.service_id))

            await self._spin_for_response(HEARTBEAT_TIMEOUT)

            # wait for ack

            logger.debug(
                "Received heartbeat ack from service {}".format(self.service_id))
            response = recv_pipe.recv()

            if not isinstance(response, tuple) or not (1 <= len(response) <= 2):
                raise ServiceError(
                    "Service {} did not return a correct tuple to challenge".format(self.service_id))

            if response[0] == STATUS_MESSAGES.STARTUP_ERROR.value:
                err = None
                if len(response) == 2:
                    err = response[1]

                raise ServiceError("Service {} returned an error during startup: {}".format(
                    self.service_id, err), critical=True)

            if response[0] != STATUS_MESSAGES.HEARTBEAT_ACK.value:

                raise ServiceError(
                    "Service {}: returned no heartbeat ack.".format(self.service_id))

            self._report_event(True)
            return True

        except Exception as e:

            logger.debug(
                "Service {}: error during heartbeat of service {}".format(self.service_id, e))

            self.handle_error(e)

            return False

    def handle_error(self, e):
        """report error, give to list etc. TODO"""

        self.last_error = e

        def crit():
            self.logger.error(
                "Critical error causing service to stop received during service operation {}: {}".format(self.service_id, e))
            self.stop(True)

        if isinstance(e, ServiceError):
            # if service error and critical
            if e.critical:
                crit()
                return
        elif not isinstance(e, TimeoutError):
            # if not service error and not timeout
            crit()
            return

        # todo add to metrics
        self._report_event(False)

    def _report_event(self, positive):
        """For metrics"""
        self._metric_events.append(positive)

    async def start(self, is_manual=False):
        logger = self.logger

        if self.is_running:
            raise Exception(
                "Service {} already started".format(self.service_id))

        _recv_pipe_main, _send_pipe_main = Pipe(
            duplex=False)
        _recv_pipe_sensor, _send_pipe_sensor = Pipe(
            duplex=False)

        self.active_handle = SensingServiceHandle(
            send_pipe=_send_pipe_main,
            recv_pipe=_recv_pipe_sensor,
            process=self.service_class(
                self.config, _send_pipe_sensor, _recv_pipe_main
            ))

        self.active_handle.process.start()

        logger.info("Started service {}".format(self.service_id))

        self.status = SERVICE_STATUS.RUNNING

        # if manually started, make sure to turn on restart!
        if is_manual:
            self.reboot_attempts = 0
            self.last_reboot = None
            self.should_reboot = True

        heatbeat_success = await self.check_heartbeat()

        # process all started, let's try to send heartbeat
        if not heatbeat_success:

            self.status = SERVICE_STATUS.STOPPED

            self.stop(True)

    async def try_reboot(self):

        logger = self.logger

        logger.info("TRYING RESTART {}".format(self.service_id))

        if self.is_running:
            logger.info(
                "Service {} already running, not restarting".format(self.service_id))
            return

        if not self.should_reboot:
            logger.info(
                "Service {} not configured to restart".format(self.service_id))
            return

        if self.reboot_attempts >= len(REBOOT_LOOKUP_TIMEOUTS):
            logger.warning(
                "Service {} exceeded max reboot attempts, not restarting".format(self.service_id))

            self.should_reboot = False
            return

        if self.last_reboot is not None and (self.last_reboot + timedelta(
                seconds=REBOOT_LOOKUP_TIMEOUTS[self.reboot_attempts])) > datetime.now():
            logger.debug(
                "Service {} reboot not due, not restarting".format(self.service_id))
            return

        # this will prevent the restarting of the service temporarily
        self.status = SERVICE_STATUS.WAITING_TO_REBOOT

        logger.info("Trying to restart service {}, attempt num: {}".format(
            self.service_id, self.reboot_attempts))

        self.reboot_attempts += 1
        self.last_reboot = datetime.now()

        return await self.start()

    def stop(self, ill=False):

        self.terminate_handle()
        if ill:
            self.status = SERVICE_STATUS.STOPPED_ILL
        else:
            self.status = SERVICE_STATUS.STOPPED

    def __del__(self):
        self.terminate_handle()

    def __repr__(self):
        return "ServiceDelegate(status={}, errors={}, should_reboot={}, last_reboot={}, reboot_attempts={})".format(
            self.status, self.errors, self.should_reboot, self.last_reboot, self.reboot_attempts)
