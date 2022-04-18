#!/usr/bin/python
import os
from record_settings import get_record_settings


def should_start_on_boot():
    try:
        with open("../start_on_boot.txt", "r") as f:
            return f.readlines()[0].lower().index("t") != -1
    except:
        return False


if __name__ == "__main__":
    os.chdir("/home/pi/src/sensing/")
    if should_start_on_boot() and get_record_settings() is not None:
        os.system("""
if ! tmux has-session -t data_rec 2>/dev/null; then
    echo "CREATED"
    tmux new-session -d -s data_rec
    tmux send-keys -t data_rec:0 'bash' C-m
    tmux send-keys -t data_rec:0 'python /home/pi/src/sensing/main.py' C-m
    exit 0
fi
""")
