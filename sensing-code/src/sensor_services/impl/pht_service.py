from ..sensing_service import SensingService


class PHTService(SensingService):

    __id__ = "pht_service"

    i2c_address = None

    sensor = None

    def startup(self):
        try:
            import qwiic_bme280
        except ImportError:
            raise Exception("Unable to import qwiic_bme280, is it installed?")

        self.sensor = qwiic_bme280.QwiicBme280(self.i2c_address)

        if not self.sensor.is_connected():
            raise Exception(
                "Qwiic BME280 device, isn't connected to the system. Please check your connection.")

        self.sensor.begin()

    def configure(self, config):

        if config is not None:
            if "i2c_address" in config:
                self.i2c_address = config["i2c_address"]

    def teardown(self):
        if self.sensor is not None:
            del self.sensor

    def read_data(self):

        if self.sensor is None:
            raise Exception("No PHT Sensor")

        return {
            "temp_celcius": float(self.sensor.temperature_celsius),
            "pressure_hpa": float(self.sensor.pressure/1e4),
            "humidity_rh": float(self.sensor.humidity)
        }

    @staticmethod
    def get_keys():
        return ["temp_celcius", "pressure_hpa", "humidity_rh"]

    @staticmethod
    def speak_data(data):
        if data is None or not isinstance(data, dict):
            return
        return "Temperature: {:.1f}C, Pressure: {:.1f}hPa, Humidity: {:.1f}%".format(data.get("temp_celcius"), data.get("pressure_hpa"), data.get("humidity_rh"))
