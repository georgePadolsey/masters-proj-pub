from ..sensing_service import SensingService


class CO2Service(SensingService):

    __id__ = "co2_service"

    i2c_address = None

    sensor = None

    def startup(self):
        try:
            import busio
            import adafruit_ccs811
            from board import I2C
        except ImportError:
            raise Exception(
                "Unable to import busio/adafruit_ccs811, is it installed?")

        i2c = I2C()   # uses board.SCL and board.SDA
        self.sensor = adafruit_ccs811.CCS811(i2c, address=0x5B)

    def configure(self, config):
        pass

    def teardown(self):
        if self.sensor is not None:
            del self.sensor

    def read_data(self):

        if self.sensor is None:
            raise Exception("No CO2 Sensor")

        if not self.sensor.data_ready:
            return None

        return {
            "eco2": self.sensor.eco2,
            "tvoc": self.sensor.tvoc
        }

    @staticmethod
    def get_keys():
        return ["eco2", "tvoc"]

    @staticmethod
    def speak_data(data):
        if data is None or not isinstance(data, dict):
            return
        return "eCO2: {}, TVOC: {}".format(data.get("co2"), data.get("tvoc"))
