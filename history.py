import os
import time

MAX_HISTORY = 5
HISTORY_DIR = "kubios_history"

# Create directory if it dosen't exist
try:
    os.mkdir(HISTORY_DIR)
except OSError:
    pass

# History files list
def get_history_files():
    files = [f for f in os.listdir(HISTORY_DIR) if f.startswith("kubios") and f.endswith(".txt")]
    files.sort()
    files = [HISTORY_DIR + "/" + f for f in files]
    return files

# Saving history to file
def save_to_history_file(data):
    t = time.localtime(time.time())
    filename = "kubios_{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}.txt".format(t[0], t[1], t[2], t[3], t[4], t[5])
    filepath = HISTORY_DIR + "/" + filename
    display_time = "{:02d}:{:02d}:{:02d} {:02d}.{:02d}.{:04d}".format(t[3], t[4], t[5], t[2], t[1], t[0])
    try:
        with open(filepath, "w") as f:
            f.write("Date: {}\n\n".format(display_time))
            f.write("Mean HR: {:.0f}\n".format(data.get("mean_hr_bpm", 0)))
            f.write("Mean PPI: {:.0f}\n".format(data.get("mean_rr_ms", 0)))
            f.write("RMSSD: {:.0f}\n".format(data.get("rmssd_ms", 0)))
            f.write("SDNN: {:.0f}\n".format(data.get("sdnn_ms", 0)))
            f.write("SNS: {:.2f}\n".format(data.get("sns_index", 0)))
            f.write("PNS: {:.2f}\n".format(data.get("pns_index", 0)))

    except OSError as e:
        print("Failed to save history file:", e)

# History list
def list_history_files():
    files = get_history_files()
    for i, f in enumerate(files):
        print("[{}] {}".format(i + 1, f.split("/")[-1]))
    return files

# History printing
def print_history_file(index):
    files = get_history_files()
    if 0 <= index < len(files):
        try:
            with open(files[index], "r") as f:
                print(f.read())
        except OSError as e:
            print("Failed to read history file:", e)
    else:
        print("Not valid option!")
# Remove old files
def prune_history_keep():
    files = get_history_files()
    if len(files) >= MAX_HISTORY:
        oldest = files[0]
        try:
            os.remove(oldest)
        except OSError as e:
            print("Err", e)
        
prune_history_keep()