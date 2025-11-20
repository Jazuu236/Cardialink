# Peak detection and timestamping
def detect_peaks(data, threshold, sampling_interval):
    peaks = []
    in_region = False
    max_val = None
    max_index = None
    
    for i, val in enumerate(data):
        if val > threshold:
            if not in_region:
                in_region = True
                max_val = val
                max_index = i
            else:
                if val > max_val:
                    max_val = val
                    max_index = i
        else:
            if in_region:
                timestamp_ms = max_index * sampling_interval
                peaks.append((timestamp_ms, max_val))
                in_region = False
                max_val = None
                max_index = None
                
    if in_region:
        timestamp_ms = max_index * sampling_interval
        peaks.append((timestamp_ms, max_val))
    
    return peaks
