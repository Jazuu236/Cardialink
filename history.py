import os
import time

MAX_HISTORY = 5
HISTORY_DIR = "kubios_history"

# Create directory if it dosen't exist
if HISTORY_DIR not in os.listdir():
    os.mkdir(HISTORY_DIR)

# History files list
def get_history_files():
    files = [f for f in os.listdir(HISTORY_DIR) if f.startswith("kubios") and f.endswith(".txt")]
    files.sort()
    files = [HISTORY_DIR + "/" + f for f in files]
    return files

# Saving history to file
def save_to_history_file(data):
    t = time.localtime()
    filename = "kubios_{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}.txt".format(t[0], t[1], t[2], t[3], t[4], t[5])
    filepath = HISTORY_DIR + "/" + filename
    display_time = "{:02d}:{:02d}:{:02d} {:02d}.{:02d}.{:04d}".format(t[3], t[4], t[5], t[2], t[1], t[0])

    with open(filepath, "w") as f:
        f.write("Created: {}\n\n".format(display_time))
        f.write("Mean HR: {}\n".format(data.get("mean_hr_bpm")))
        f.write("Mean PPI: {}\n".format(data.get("mean_rr_ms")))
        f.write("RMSSD: {}\n".format(data.get("rmssd_ms")))
        f.write("SDNN: {}\n".format(data.get("sdnn_ms")))
        f.write("SNS: {}\n".format(data.get("sns_index")))
        f.write("PNS: {}\n".format(data.get("pns_index")))

# Deleting old files over the file limit
files = get_history_files()
if len(files) > MAX_HISTORY:
    for old_file in files[:-MAX_HISTORY]:
        os.remove(old_file)

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
        with open(files[index], "r") as f:
            print(f.read())
    else:
        print("Not valid option!")