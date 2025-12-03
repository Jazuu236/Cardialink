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

    #Filter illegally close intervals (limit 300ms)
    filtered_peaks = []
    for i in range(len(peaks)):
        ts, val = peaks[i]
        too_close = False
        for j in range(len(peaks)):
            if i == j:
                continue
            ts2, val2 = peaks[j]
            if abs(ts - ts2) <= 300 and val2 > val:
                too_close = True
                break
        if not too_close:
            filtered_peaks.append((ts, val))
    
    
    return filtered_peaks

# Get peak to peak values for kubios
def extract_ppi(measurer):
    # Check for data
    if len(measurer.CACHE_STORAGE_DYNAMIC) <= 2:
        return []
    # Calculate treshold atuomatically
    avg_val = measurer.cache_get_average_value(measurer.CACHETYPE_DYNAMIC)
    peak_avg = measurer.dynamic_cache_get_average_peak_value()
    threshold = avg_val + (peak_avg - avg_val) * 0.6
    # Detect peaks
    peaks = detect_peaks(measurer.CACHE_STORAGE_DYNAMIC, threshold, 10)

    # Get intervals
    ppi_list = []
    for k in range(1, len(peaks)):
        diff = peaks[k][0] - peaks[k-1][0]
        # Filter unrealistic values (300ms - 2000ms)
        if 300 < diff < 2000:
            ppi_list.append(diff)
            
    return ppi_list
