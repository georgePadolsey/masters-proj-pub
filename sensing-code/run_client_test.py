#!/usr/bin/python
import sys
from src.sensing_client import SensingClient

from src.sensor_services.sensing_service_manager import SensingServiceManager

from src.sensor_services.impl.example_service import ExampleService
from src.sensor_services.impl.example_service_long import ExampleServiceLong


if __name__ == "__main__":
    reboot_mode = False
    if "--on-reboot" in sys.argv:
        reboot_mode = True

    example_services = [ExampleService, ExampleServiceLong]

    service_manager = SensingServiceManager(
        example_services
    )
    SensingClient(service_manager=service_manager)
