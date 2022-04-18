import qwiic_bme280
import time
import sys
import plotext as plt
import numpy as np
import pandas as pd

from rich.console import Console
from rich.markdown import Markdown
from rich import print
from rich.prompt import Prompt
from rich.prompt import Confirm
import inquirer
from rich.live import Live
from rich.table import Table
import signal
from datetime import datetime
import json
import csv
import os
import math
from record_settings import get_record_settings

from rich.progress import Progress
from ublox_gps import UbloxGps
import serial

from rich.progress import track


ENABLED_FLAGS = ["GPS_UBLOX", "PHT_Sense"]


def resume_record():

    mySensor = qwiic_bme280.QwiicBme280()
    if not mySensor.connected:
        error_console.print(
            "[bold red]The Qwiic BME280 device isn't connected to the system. Please check your connection[/bold red]")
        console.input(
            "[bold red]The Qwiic BME280 device isn't connected to the system. Please check your connection[/bold red]\nPress enter to continue")
        return

    mySensor.begin()

    plt.clt()
    header_text()

    record_settings = get_record_settings()

    if record_settings is None:
        console.print("No record settings")
        return

    data_file_name = "s{}-e{}-f{:.0f}.csv".format(
        int(datetime.timestamp(record_settings["start_time"]) * 1000),
        int(datetime.timestamp(record_settings["end_time"]) * 1000),
        record_settings["recording_frequency"])

    data_file_path = "data/{}".format(data_file_name)

    console.print("Start time:", record_settings["start_time"])
    console.print("End time:", record_settings["end_time"])
    console.print("Recording Frequency: {} Hz".format(
        record_settings["recording_frequency"]))
    console.print("Data File Path:", data_file_path)

    console.print()

    full_duration = datetime.timestamp(
        record_settings["end_time"]) - datetime.timestamp(record_settings["start_time"])

    with open(data_file_path, "a") as f:

        writer = csv.writer(f)

        # if at start of file
        if f.tell() == 0:
            writer.writerow(["Timestamp", "Temperature (C)",
                            "Pressure (hPa)", "Humidity (% RH)"])

        writer.writerow(["Resuming" * 4])

        with Progress() as progress:

            task1 = progress.add_task(
                "[red]Recording data...", total=full_duration)

            while datetime.now() < record_settings["end_time"]:

                # write a row to the csv file
                writer.writerow([datetime.timestamp(datetime.now()),
                                 mySensor.temperature_celsius,
                                 mySensor.pressure/1e4,
                                 mySensor.humidity])

                time.sleep(1/record_settings["recording_frequency"])
                progress.update(task1, completed=full_duration - (datetime.timestamp(
                    record_settings["end_time"]) - datetime.timestamp(datetime.now())))

    console.input(
        "\n[bold green]Recording has completed\nPress enter to continue")
    return


def ctrl_c_handler(*args):
    global ctrl_c_flag

    if ctrl_c_flag:
        plt.clt()
        console.print("[yellow]Goodbye![/yellow]")
        sys.exit(0)
    ctrl_c_flag = True


def header_text():
    console.print("="*30, justify="center")
    console.print(
        "[bold yellow] :earth_americas: Environmental Sensing Platform :earth_africa: [/bold yellow]", justify="center")
    console.print("="*30, justify="center")

    gps_status = "[orange bold]⚠️"  # if gps_enabled else "❌"
    pht_status = "✅"
    console.print("[white bold]Status:\nGPS: {} PHT: {}".format(
        gps_status, pht_status), justify="center")
    console.print("")


def should_start_on_boot():
    try:
        with open("start_on_boot.txt", "r") as f:
            return f.readlines()[0].lower().index("t") != -1
    except:
        return False


def toggle_start_on_boot():

    orig = should_start_on_boot()

    with open("start_on_boot.txt", "w+") as f:
        f.write(str(not orig))


def is_time_delta(x):
    try:
        pd.Timedelta(x)
        return True
    except:
        return False


def validate_prompt(text, validate_fn=None):
    out = None
    running = True
    while running:
        out = Prompt.ask(text)
        if validate_fn is None or validate_fn(out):
            running = False
            return out
        else:
            console.print(
                "[bold red]Invalid Value for {}[/bold red]".format(text))


def set_record_settings(record_till):

    json_data = {
        "start_time": datetime.timestamp(datetime.now()),
        "end_time": datetime.timestamp(record_till),
        "recording_frequency": 10
    }
    with open("../current_record_settings.json", "w") as f:
        json.dump(json_data, f)


def record_data_choices():
    global ctrl_c_flag
    plt.clt()

    header_text()

    time_running = pd.Timedelta(validate_prompt("Data recording length (e.g. 5m for 5 minutes)",
                                validate_fn=lambda x: len(x.strip()) != 0 and is_time_delta(x)))

    while not Confirm.ask("Running for {}".format(time_running)):
        time_running = pd.Timedelta(validate_prompt(
            "Data recording length (e.g. 5m for 5 minutes)", validate_fn=lambda x: len(x.strip()) != 0 and is_time_delta(x)))

    record_till = datetime.now() + time_running.to_pytimedelta()
    set_record_settings(record_till)

    resume_record()


def choose_action():
    global ctrl_c_flag

    plt.clt()
    header_text()

    action_choices = {"view-live-data-graph": "View Live Data (Graph)",
                      "view-live-data": "View Live Data (Log)",
                      "record-data": "Record Data",
                      "toggle-start-on-boot": "Toggle Start On Boot "+("🟢" if should_start_on_boot() else "🔴"),
                      "quit": "Quit"}
    question = [
        inquirer.List('action',
                      message="What would you like to do? (↑/↓)",
                      choices=action_choices.values(),
                      ),
    ]
    answers = inquirer.prompt(question)

    if answers is None:
        return

    flipped_action_choices = dict((v, k) for k, v in action_choices.items())

    ac_key = flipped_action_choices[answers["action"]]

    if ac_key == "view-live-data-graph":
        view_live_data_graph()
    elif ac_key == "view-live-data":
        view_live_data()
    elif ac_key == "record-data":
        record_data_choices()
    elif ac_key == "toggle-start-on-boot":
        toggle_start_on_boot()
    elif ac_key == 'quit':
        plt.clt()
        return

    choose_action()


def view_live_data():
    global ctrl_c_flag
    plt.clear_terminal()

    mySensor = qwiic_bme280.QwiicBme280()
    if not mySensor.connected:
        error_console.print(
            "[bold red]The Qwiic BME280 device isn't connected to the system. Please check your connection[/bold red]")
        console.input(
            "[bold red]The Qwiic BME280 device isn't connected to the system. Please check your connection[/bold red]\nPress enter to continue")
        return

    mySensor.begin()

    ys = []

    def update_table():
        table = Table()
        table.add_column("Datetime")
        table.add_column("Temperature (°C)")
        table.add_column("Pressure (hPa)")
        table.add_column("Humidity (RH %)")

        ys.append(["{}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")),
                   "{:.2f} °C".format(mySensor.temperature_celsius),
                   "{:.2f} hPa".format(mySensor.pressure/1e4),
                   "{:.2f} %".format(mySensor.humidity)])

        for y in ys:
            table.add_row(*y)

        return table

    with Live(update_table(), refresh_per_second=2, vertical_overflow="visible") as live:

        while True:
            live.update(update_table())

            if ctrl_c_flag:
                ctrl_c_flag = False
                return

            time.sleep(.5)


def view_live_data_graph():
    global ctrl_c_flag
    plt.clear_terminal()

    mySensor = qwiic_bme280.QwiicBme280()

    if not mySensor.connected:
        error_console.print(
            "[bold red]The Qwiic BME280 device isn't connected to the system. Please check your connection[/bold red]")
        console.input(
            "[bold red]The Qwiic BME280 device isn't connected to the system. Please check your connection[/bold red]\nPress enter to continue")
        return

    mySensor.begin()

    SIZE = 500
    ys = []

    cache_i = 0
    cache_temp = np.zeros((SIZE))
    cache_pressure = np.zeros((SIZE))
    cache_humidity = np.zeros((SIZE))

    MIN_VAL_TEMP = 18
    MAX_VAL_TEMP = 25

    MIN_VAL_PRESSURE = 10.225
    MAX_VAL_PRESSURE = 10.35

    MIN_VAL_HUMIDITY = 1
    MAX_VAL_HUMIDITY = 100

    plt.subplots(1, 3)

    TITLES = ["Temperature (C)", "Pressure (hPa)", "Humidity (RH %)"]

    for i in range(1, 4):
        plt.subplot(1, i)
        plt.title(TITLES[i-1])
        plt.clc()

    i = 0
    while True:
        plt.clt()
        # print("Humidity:\t%.3f" % mySensor.humidity)

        # print("Pressure:\t%.3f" % mySensor.pressure)

        if cache_i == 0:
            cache_temp[:] = MIN_VAL_TEMP
            cache_temp[-1] = MAX_VAL_TEMP

            cache_pressure[:] = MIN_VAL_PRESSURE
            cache_pressure[-1] = MAX_VAL_PRESSURE

            cache_humidity[:] = MIN_VAL_HUMIDITY
            cache_humidity[-1] = MAX_VAL_HUMIDITY

        cache_temp[cache_i] = float(mySensor.temperature_celsius)
        cache_pressure[cache_i] = float(mySensor.pressure)/1e4

        cache_humidity[cache_i] = float(mySensor.humidity)

        cache_i = (cache_i + 1) % SIZE

        # print("Altitude:\t%.3f" % mySensor.altitude_meters)

        # print("Temperature:\t%.2f" % mySensor.temperature_celsius)

        # print("")

        plt.subplot(1, 1)
        plt.cld()

        plt.plot(cache_temp)

        plt.subplot(1, 2)
        plt.cld()

        plt.plot(cache_pressure)

        plt.subplot(1, 3)
        plt.cld()

        plt.plot(cache_humidity)

        if ctrl_c_flag:
            ctrl_c_flag = False
            return
        plt.sleep(.1)
        plt.show()

        # print(cache)
    print("done")


if __name__ == "__main__":

    console = Console()
    error_console = Console(stderr=True)
    # gps_enabled = True
    # try:
    #     port = serial.Serial('/dev/serial0', baudrate=38400, timeout=1)
    #     gps = UbloxGps(port)
    # except serial.serialutil.SerialException as e:
    #     print(e)
    #     console.print("[red bold]Unable to open GPS Serial port")
    #     gps_enabled = False

    # try:
    #     print("Listenting for UBX Messages.")
    #     while True:
    #         try:
    #             coords = gps.geo_coords()
    #             print(coords.lon, coords.lat)
    #         except (ValueError, IOError) as err:
    #             print(err)
    # finally:
    #     port.close()
    # import sys
    # sys.exit(0)

    ctrl_c_flag = False
    signal.signal(signal.SIGINT, ctrl_c_handler)

    if get_record_settings() is None:
        choose_action()
    else:
        console.print("[purple]Resuming!")
        resume_record()
