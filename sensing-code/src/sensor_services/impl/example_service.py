from random import random
import time
from ..sensing_service import SensingService


class ExampleService(SensingService):

    __id__ = "example_service"

    def configure(self, config):
        # if random() < 0.1:
        #     raise Exception("AH")

        if config is not None:
            if "failure_rate" in config:
                self.test = config["test"]
        return

    def startup(self):
        # if random() < 0.1:
        #     raise Exception("AH")
        return

    def read_data(self):
        time.sleep(random() * .1)
        # if random() < 0.1:
        #     raise Exception("AH")
        return {"test": time.time()}

    def teardown(self):
        return

    @staticmethod
    def get_keys():
        return {
            "test"
        }

    @staticmethod
    def speak_data(data):
        if data is None or not isinstance(data, dict):
            return
        return "Time: {:.5f}".format(data["test"])
