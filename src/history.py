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
    try:
        files = [f for f in os.listdir(HISTORY_DIR) if f.startswith("kubios") and f.endswith(".txt")]
        files.sort(reverse=True)
        files = [HISTORY_DIR + "/" + f for f in files]
        return files
    except OSError:
        return []

# Saving history to file
def save_to_history_file(data):
    t = time.localtime(time.time())
    filename = "kubios_{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}.txt".format(t[0], t[1], t[2], t[3], t[4], t[5])
    filepath = HISTORY_DIR + "/" + filename
    
    # Separate Date and Time strings
    date_str = "{:02d}.{:02d}.{:04d}".format(t[2], t[1], t[0])
    time_str = "{:02d}:{:02d}:{:02d}".format(t[3], t[4], t[5])
    
    try:
        with open(filepath, "w") as f:
            f.write("Date: {}#".format(date_str))
            f.write("Time: {}#".format(time_str))
            
            if isinstance(data, dict):
                f.write("Mean HR: {:.0f}#".format(data.get("mean_hr_bpm", 0)))
                f.write("Mean PPI: {:.0f}#".format(data.get("mean_rr_ms", 0)))
                f.write("RMSSD: {:.0f}#".format(data.get("rmssd_ms", 0)))
                f.write("SDNN: {:.0f}#".format(data.get("sdnn_ms", 0)))
                f.write("SNS: {:.2f}\n".format(data.get("sns_index", 0)) + "#")
                f.write("PNS: {:.2f}\n".format(data.get("pns_index", 0)) + "#")
                f.write("Stress: {:.1f}#".format(data.get("stress_index", 0)))
                f.write("Readiness: {:.1f}#".format(data.get("readiness", 0)))
                f.write("Press to return")
            else:
                f.write("Raw: " + str(data) + "#")
        
        print(f"DEBUG: Saved to {filepath}")
        
        prune_history_keep()

    except OSError as e:
        print("Failed to save history file:", e)

# Remove old files
def prune_history_keep():
    files = get_history_files()

    while len(files) > MAX_HISTORY:
        oldest = files[-1] 
        try:
            print(f"DEBUG: Pruning old file {oldest}")
            os.remove(oldest)
            files = get_history_files()
        except OSError as e:
            print("Can't remove old files", e)
            break

# Return file as a string
def get_history_content(index):
    files = get_history_files()
    if 0 <= index < len(files):
        try:
            with open(files[index], "r") as f:
                return f.read()
        except OSError as e:
            return "Error reading file"
    else:
        return "File not found"

print(f"History files count: {len(get_history_files())}")


