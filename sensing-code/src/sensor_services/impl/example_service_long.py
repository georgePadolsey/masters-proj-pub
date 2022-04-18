from random import random
import time
from ..sensing_service import SensingService


class ExampleServiceLong(SensingService):

    __id__ = "example_service_long"

    def configure(self, config):
        # if random() < 0.1:
        #     raise Exception("AH")

        if config is not None:
            if "failure_rate" in config:
                self.test = config["test"]
        return

    def startup(self):
        if random() < 0.25:
            raise Exception("AH")
        return

    def read_data(self):
        # if random() < 0.1:
        #     raise Exception("AH")
        time.sleep(random() * 2)
        return {"test_long": time.time()}

    def teardown(self):
        return

    @staticmethod
    def get_keys():
        return [
            "test_long"
        ]

    @staticmethod
    def speak_data(data):
        if data is None or not isinstance(data, dict):
            return
        return "Time: {:.5f}".format(data["test"])
