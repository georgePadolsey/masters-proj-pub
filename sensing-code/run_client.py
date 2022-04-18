#!/usr/bin/python
import sys
from src.sensing_client import SensingClient

from src.sensor_services.sensing_service_manager import SensingServiceManager

from src.sensor_services.impl.gps_service import GPSService
from src.sensor_services.impl.pht_service import PHTService
from src.sensor_services.impl.dust_service import DustService

from src.sensor_services.impl.co2_service import CO2Service

if __name__ == "__main__":
    reboot_mode = False
    if "--on-reboot" in sys.argv:
        reboot_mode = True

    service_manager = SensingServiceManager(
        (GPSService,
         PHTService,
         DustService,
         CO2Service)
    )

    service_manager.configure_service('gps_service', {
        "baud_rate": 38400,
        "serial_port": "/dev/serial0",
        "serial_timeout": 1
    })

    SensingClient(service_manager=service_manager)
