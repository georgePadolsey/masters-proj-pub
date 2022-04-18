from ..sensing_service import SensingService


class DustService(SensingService):

    __id__ = "dust_service"

    udp_ip = "10.11.97.100"
    udp_port = 10080

    sock = None

    def configure(self, config):
        if config is not None:
            if "udp_ip" in config:
                self.udp_ip = config["udp_ip"]

            if "udp_port" in config:
                self.udp_port = config["udp_port"]

        self.get_logger().debug(
            "Configured sensor with udp address {}:{}".format(self.udp_ip, self.udp_port))

    def startup(self):
        try:
            import socket
        except ImportError:
            raise Exception("No socket module found")

        logger = self.get_logger()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.bind((self.udp_ip, self.udp_port))
        except OSError:
            raise Exception(
                "Unable to bind to requested address, ensure you have configured the raspberry pi's network as defined in POPS manual.")
        logger.info("Succesfully bound to socket {}:{}".format(
            self.udp_ip, self.udp_port))

    def teardown(self):
        if self.sock is not None:
            self.sock.close()

    def read_data(self):

        logger = self.get_logger()
        if self.sock is None:
            raise Exception("no Socket!")

        data, addr = self.sock.recvfrom(1024)

        s_data = data.decode('utf-8')

        cols = [
            "MagicPops", "MagicPopsVersion", "CsvFileName",
            # csv headers:

            "DateTime", "TimeSSM", "Status", "DateStatus", "PartCt", "HistSum", "PartCon", "BL", "BLTH", "STD", "MaxSTD", "P", "TofP", "PumpLife_hrs", "WidthSTD", "AveWidth", "POPS_Flow",
            "PumpFB", "LDTemp", "LaserFB", "LD_Mon", "Temp", "BatV", "Laser_Current", "Flow_Set", "BL_Start", "TH_Mult", "nbins", "logmin", "logmax", "Skip_Save", "MinPeakPts", "MaxPeakPts", "RawPts"
            # ... followed by bins starting at b0 -> b[nbins -1]
        ]

        first_line = s_data.split('\r\n')[0]
        split_first_line = first_line.split(',')

        if split_first_line[0] != 'POPS':
            raise Exception("Failed to get magic value 'POPS'")
        if split_first_line[1] != 'POPS-220':
            logger.warning(
                "Invalid magic value {}!='POPS-220'. This may indicate the dust sensor is using a different/updated firmware. It may cause no issues, but be aware!")

        try:
            nbins = int(split_first_line[cols.index("nbins")])
        except ValueError:
            raise Exception("Invalid number of bins in data sensor reading {}".format(
                split_first_line[cols.index("nbins")]))

        cols += ["b{}".format(i) for i in range(nbins)]

        if len(cols) != len(split_first_line):
            logger.warning(
                "Predicted length of data sensor data doesn't match actual length")

        return dict(zip(cols, split_first_line))
        # logger = self.get_logger()
        # if self.sensor is None:
        #     logger.critical(
        #         "No BME280 sensor is present at time of reading data, has it been deleted by another thread?")
        #     raise Exception("No PHT Sensor")

        # logger.debug("Read data from sensor, Temp Celcius: {}, Pressure HPa: {}, Humidity RH: {}".format(
        #     self.sensor.temperature_celsius, float(self.sensor.pressure/1e4), float(self.sensor.humidity)))
        # return {
        #     "temp_celcius": float(self.sensor.temperature_celsius),
        #     "pressure_hpa": float(self.sensor.pressure/1e4),
        #     "humidity_rh": float(self.sensor.humidity)
        # }

    @staticmethod
    def get_keys():
        return [
            "MagicPops", "MagicPopsVersion", "CsvFileName",
            # csv headers:
            "DateTime", "TimeSSM", "Status", "DateStatus", "PartCt", "HistSum", "PartCon", "BL", "BLTH", "STD", "MaxSTD", "P", "TofP", "PumpLife_hrs", "WidthSTD", "AveWidth", "POPS_Flow",
            "PumpFB", "LDTemp", "LaserFB", "LD_Mon", "Temp", "BatV", "Laser_Current", "Flow_Set", "BL_Start", "TH_Mult", "nbins", "logmin", "logmax", "Skip_Save", "MinPeakPts", "MaxPeakPts",
            "RawPts",
            # ... followed by bins starting at b0 -> b[nbins -1]
            "b0", "b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8", "b9", "b10", "b11", "b12", "b13", "b14", "b15"
        ]

    @staticmethod
    def speak_data(data):
        if data is None or not isinstance(data, dict):
            return
        return "Running dust sensor, Temperature: {:.1f}, Pressure: {:.1f}, Concentration: {:1f}".format(data.get("TofP"),
                                                                                                         data.get("P"), data.get("PartCt"))
