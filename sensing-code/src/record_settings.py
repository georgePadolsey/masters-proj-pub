import os
import json

from datetime import datetime


def get_record_settings():
    settings = {}
    try:
        with open("../current_record_settings.json", "r") as f:
            record_settings = json.load(f)

            from_time = datetime.fromtimestamp(record_settings["start_time"])
            to = datetime.fromtimestamp(record_settings["end_time"])
            if datetime.now() > to:
                return None

            if from_time > to:
                return None

            settings["start_time"] = from_time
            settings["end_time"] = to

            settings["recording_frequency"] = float(
                record_settings["recording_frequency"])
            assert settings["recording_frequency"] > 0, "Recording frequency must be positive!"

        return settings
    except Exception as e:
        try:
            os.remove("current_record_settings.json")
        except OSError:
            pass

        raise Exception(
            "Unable to read record settings, failed due to error "+str(e))
