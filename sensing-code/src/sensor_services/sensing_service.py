
from multiprocessing import Process
from abc import ABCMeta, abstractmethod
import logging
import time

from ..utils.logging_utils import get_cur_logger_dir
from ..utils.status_utils import STATUS_MESSAGES


class SensingService(Process, metaclass=ABCMeta):

    _logger = None

    _config = None

    def __init__(self, config, _send_pipe_to_main, _recv_pipe_from_main):
        super(SensingService, self).__init__(daemon=True)
        self._config = config
        self._send_pipe_to_main = _send_pipe_to_main
        self._recv_pipe_from_main = _recv_pipe_from_main
        # self.start()

    def run(self):

        logger = self.get_logger()

        if self._send_pipe_to_main is None or self._recv_pipe_from_main is None:
            logger.critical("Pipes to main thread are not set")
            return

        try:
            # Startup Sequence
            startup_error = None
            try:
                self.configure(self._config)
                self.startup()
            except Exception as e:
                startup_error = e
                logger.error("Startup Error: {}".format(e))
            # End startup sequence

            logger.info("Startup sequence finished")

            while True:

                # wait for poll
                if self._recv_pipe_from_main.poll():

                    challenge = self._recv_pipe_from_main.recv()

                    logger.debug("Received challenge: {}".format(challenge))

                    if not isinstance(challenge, tuple):
                        logger.error("Challenge is not a tuple")
                        continue

                    if not(1 <= len(challenge) <= 2):
                        logger.error("Challenge has wrong length")
                        continue

                    challenge_type = challenge[0]
                    # challenge_data = challenge[1] not needed but included for completeness

                    if challenge_type == STATUS_MESSAGES.HEARTBEAT_SYN.value:

                        if startup_error is not None:
                            self._send_pipe_to_main.send(
                                (STATUS_MESSAGES.STARTUP_ERROR.value, startup_error))
                            logger.debug("Sent startup error")
                        else:
                            self._send_pipe_to_main.send(
                                (STATUS_MESSAGES.HEARTBEAT_ACK.value,))
                            logger.debug("Sent heartbeat ack")

                    elif challenge_type == STATUS_MESSAGES.GET_DATA.value:

                        try:
                            data = self.read_data()
                        except Exception as e:
                            self._send_pipe_to_main.send(
                                (STATUS_MESSAGES.DATA_ERROR.value, e))
                            logger.debug("Sent data error {}".format(e))

                            time.sleep(.01)
                            continue

                        if data is None:
                            self._send_pipe_to_main.send(
                                (STATUS_MESSAGES.DATA_ERROR.value, "No data returned"))
                            logger.debug("Sent data error")
                        else:
                            self._send_pipe_to_main.send(
                                (STATUS_MESSAGES.DATA_OK.value, data))
                            logger.debug("Sent data ok")

                    elif challenge_type == STATUS_MESSAGES.STOP.value:
                        logger.debug("Received stop")
                        break

                # max sampling rate = 100Hz
                time.sleep(.01)
        except Exception as e:
            logger.error("Error in main loop: {}".format(e))
        finally:
            self.teardown()
            logger.info("Teardown sequence finished")

    def get_logger(self):

        if self._logger is not None:
            return self._logger

        self._logger = logging.getLogger(type(self).__name__)

        if self._logger.handlers:
            return self._logger

        logfile_dir = get_cur_logger_dir()

        logfile = "{}/{}.log".format(logfile_dir, type(self).__name__)

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

    def __del__(self):

        if self._recv_pipe_from_main is not None:
            self._recv_pipe_from_main.close()
        if self._send_pipe_to_main is not None:
            self._send_pipe_to_main.close()
        self.teardown()

    @abstractmethod
    def configure(self, config):
        raise NotImplementedError()

    @abstractmethod
    def startup(self):
        raise NotImplementedError()

    @abstractmethod
    def read_data(self):
        raise NotImplementedError()

    @abstractmethod
    def teardown(self):
        raise NotImplementedError()
