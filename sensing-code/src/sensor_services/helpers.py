import time


class SERVICE_STATUS:
    STOPPED_ILL = -1
    NOT_STARTED = 0
    RUNNING = 1
    STOPPED = 2
    WAITING_TO_REBOOT = 3


class SensingServiceHandle:

    def __init__(self, send_pipe, recv_pipe, process) -> None:
        self.send_pipe = send_pipe
        self.recv_pipe = recv_pipe
        self.process = process

    def __repr__(self):
        return "SensingServiceHandle(send_pipe={}, recv_pipe={}, process={}, last_error={})".format(
            self.send_pipe, self.recv_pipe, self.process, self.last_error)

    def __str__(self):
        return "SensingServiceHandle(send_pipe={}, recv_pipe={}, process={}, last_error={})".format(
            self.send_pipe, self.recv_pipe, self.process, self.last_error)

    def __del__(self):

        self.process.terminate()
        self.process.join()

        try:
            self.send_pipe.close()
            self.recv_pipe.close()
        except Exception as e:
            print(e)

        del self.send_pipe
        del self.recv_pipe
        del self.process


class ServiceError(Exception):

    def __init__(self, msg, critical=False) -> None:
        super().__init__(msg)
        self.time = time.time()
        self.critical = critical
