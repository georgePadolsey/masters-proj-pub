#!/usr/bin/python
import os
import time

# def should_start_on_boot():
#     try:
#         with open("../start_on_boot.txt", "r") as f:
#             return f.readlines()[0].lower().index("t") != -1
#     except:
#         return False


if __name__ == "__main__":
    # sleep before starting
    time.sleep(10)
    os.chdir("/home/pi/src/sensing/")
    os.system("""
if ! tmux has-session -t data_rec 2>/dev/null; then
    echo "CREATED"
    tmux new-session -d -s data_rec
    tmux send-keys -t data_rec:0 'bash' C-m
    tmux send-keys -t data_rec:0 'sudo python /home/pi/src/sensing/run_client.py' C-m
    exit 0
fi
""")
