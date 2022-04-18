"""
CCS811 Air Quality Sensor Example Code
Author: Sasa Saftic (sasa@infincube.si)
infincube d.o.o.
Date: June 8th, 2017
License: This code is public domain

from https://github.com/sparkfun/CCS811_Air_Quality_Breakout/blob/master/Software/ccs811.py

Based on Sparkfuns Example code written by Nathan Seidle

Read the TVOC and CO2 values from the SparkFun CSS811 breakout board

A new sensor requires at 48-burn in. Once burned in a sensor requires
20 minutes of run in before readings are considered good.

Tested on Raspberry Pi Zero W
"""

from smbus import SMBus
import time

CCS811_ADDR = 0x5B  # default I2C Address

CSS811_STATUS = 0x00
CSS811_MEAS_MODE = 0x01
CSS811_ALG_RESULT_DATA = 0x02
CSS811_RAW_DATA = 0x03
CSS811_ENV_DATA = 0x05
CSS811_NTC = 0x06
CSS811_THRESHOLDS = 0x10
CSS811_BASELINE = 0x11
CSS811_HW_ID = 0x20
CSS811_HW_VERSION = 0x21
CSS811_FW_BOOT_VERSION = 0x23
CSS811_FW_APP_VERSION = 0x24
CSS811_ERROR_ID = 0xE0
CSS811_APP_START = 0xF4
CSS811_SW_RESET = 0xFF


class CCS811:
    def __init__(self, logger):
        self.logger = logger
        self.device = SMBus(1)  # self.pi.i2c_open(1, 0x5B)
        self.i2c_address = CCS811_ADDR
        self.tVOC = 0
        self.CO2 = 0

    def __del__(self):
        del self.device

    def print_error(self):
        error = self.device.read_byte_data(self.i2c_address, CSS811_ERROR_ID)
        message = 'Error: '

        if error & 1 << 5:
            message += 'HeaterSupply '
        elif error & 1 << 4:
            message += 'HeaterFault '
        elif error & 1 << 3:
            message += 'MaxResistance '
        elif error & 1 << 2:
            message += 'MeasModeInvalid '
        elif error & 1 << 1:
            message += 'ReadRegInvalid '
        elif error & 1 << 0:
            message += 'MsgInvalid '

        self.logger.debug(message)

    def check_for_error(self):
        value = self.device.read_byte_data(self.i2c_address, CSS811_STATUS)
        return value & 1 << 0

    def app_valid(self):
        value = self.device.read_byte_data(self.i2c_address, CSS811_STATUS)
        return value & 1 << 4

    def set_drive_mode(self, mode):
        if mode > 4:
            mode = 4

        setting = self.device.read_byte_data(
            self.i2c_address, CSS811_MEAS_MODE)
        setting &= ~(0b00000111 << 4)
        setting |= (mode << 4)
        self.device.write_byte_data(
            self.i2c_address, CSS811_MEAS_MODE, setting)

    def configure_ccs811(self):
        hardware_id = self.device.read_byte_data(
            self.i2c_address, CSS811_HW_ID)

        if hardware_id != 0x81:
            raise ValueError('CCS811 not found. Please check wiring.')

        if self.check_for_error():
            self.print_error()
            raise ValueError('Error at Startup.')

        if not self.app_valid():
            raise ValueError('Error: App not valid.')

        self.device.write_byte(self.i2c_address, CSS811_APP_START)

        if self.check_for_error():
            self.print_error()
            raise ValueError('Error at AppStart.')

        self.set_drive_mode(1)

        if self.check_for_error():
            self.print_error()
            raise ValueError('Error at setDriveMode.')

    def setup(self):
        self.logger.debug('Starting CCS811 Read')
        self.configure_ccs811()

        result = self.get_base_line()

        self.logger.debug("baseline for this sensor: 0x")
        if result < 0x100:
            self.logger.debug('0')
        if result < 0x10:
            self.logger.debug('0')
        self.logger.debug(result)

    def get_base_line(self):
        b = self.device.read_i2c_block_data(
            self.i2c_address, CSS811_BASELINE, 2)
        baselineMSB = b[0]
        baselineLSB = b[1]
        baseline = (baselineMSB << 8) | baselineLSB
        return baseline

    def data_available(self):
        value = self.device.read_byte_data(self.i2c_address, CSS811_STATUS)
        return value & 1 << 3

    def run(self):

        self.setup()

        while True:
            if self.data_available():
                self.read_logorithm_results()

                self.logger.debug("CO2[%d] tVOC[%d]" % (self.CO2, self.tVOC))

            elif self.check_for_error():
                self.print_error()

            time.sleep(1)

    def get_data(self):
        return self.read_logorithm_results() if self.data_available() else None

    def read_logorithm_results(self):
        d = self.device.read_i2c_block_data(
            self.i2c_address, CSS811_ALG_RESULT_DATA, 4)

        co2MSB = d[0]
        co2LSB = d[1]
        tvocMSB = d[2]
        tvocLSB = d[3]

        self.CO2 = (co2MSB << 8) | co2LSB
        self.tVOC = (tvocMSB << 8) | tvocLSB
