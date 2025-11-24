# HRV analysis from Peak to Peak Interval(PPI)
def hrv_analysis(ppi_data):
    # Mean PPI
    mean_ppi = round(sum(ppi_data) / len(ppi_data))
    mean_ppi = int(mean_ppi)
    
    # Mean HR
    mean_hr = int(round(60000 / mean_ppi))
    
    # SDNN
    sdnn = round((sum((x - mean_ppi) ** 2 for x in ppi_data) / (len(ppi_data) - 1)) ** 0.5)
    
    # RMSSD
    diffs = [(ppi_data[i+1] - ppi_data[i]) ** 2 for i in range(len(ppi_data)-1)]
    rmssd = round((sum(diffs) / len(diffs)) ** 0.5)

    return {
        "Mean_PPI": mean_ppi,
        "Mean_HR": mean_hr,
        "SDNN": sdnn,
        "RMSSD": rmssd
    }
# TEST DATA
peak_to_peak_interval = []

print(hrv_analysis(peak_to_peak_interval))