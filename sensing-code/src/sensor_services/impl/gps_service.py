from ..sensing_service import SensingService
from datetime import datetime, timezone


class GPSService(SensingService):

    __id__ = "gps_service"

    serial_port = None
    baud_rate = None
    timeout = None

    port = None
    gps = None

    def configure(self, config):

        if config is not None:
            if "serial_port" in config:
                self.serial_port = config["serial_port"]
            if "baud_rate" in config:
                self.baud_rate = config["baud_rate"]
            if "serial_timeout" in config:
                self.serial_timeout = config["serial_timeout"]

    def startup(self):

        try:
            from ublox_gps import UbloxGps
            import serial
        except ImportError:
            raise Exception(
                "Unable to import ublox_gps/serial, is it installed?")

        print("START NEW SERIAL")
        # '/dev/serial0', baudrate=38400, timeout=1)
        self.port = serial.Serial(
            self.serial_port, baudrate=self.baud_rate, timeout=self.serial_timeout)
        self.gps = UbloxGps(self.port)

    def read_data(self):
        coords = self.gps.geo_coords()  # may throw (ValueError, IOError) as err
        gps_time = self.gps.date_time()

        ts = datetime(year=gps_time.year, month=gps_time.month, day=gps_time.day,
                      hour=gps_time.hour, minute=gps_time.min, second=gps_time.sec, tzinfo=timezone.utc).timestamp()

        ts += gps_time.nano * 1e-9

        return {"lon": float(coords.lon), "lat": float(coords.lat), "time_utc": ts}

    def __del__(self):
        if self.port is not None:
            self.port.close()

            del self.gps
            del self.port

        return super().__del__()

    def teardown(self):
        if self.port is not None:
            self.port.close()

            del self.gps
            del self.port

    @staticmethod
    def get_keys():
        return [
            "lon", "lat", "time_utc"
        ]

    @staticmethod
    def speak_data(data):
        if data is None or not isinstance(data, dict):
            return
        return "Longitude: {:.4f}, Latitude: {:.4f}".format(data.get("lon"), data.get("lat"))
