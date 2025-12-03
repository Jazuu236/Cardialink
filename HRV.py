# HRV analysis from Peak to Peak Interval(PPI)
def hrv_analysis(ppi_data):

    #Prevent division by zero
    if len(ppi_data) <= 2:
        print("Not enough PPI data for HRV analysis.")
        return {
            "Mean_PPI": 0,
            "Mean_HR": 0,
            "SDNN": 0,
            "RMSSD": 0
        }
    for ppi in ppi_data:
        if ppi <= 0:
            ppi_data.remove(ppi)
        if ppi >= 2000:
            ppi_data.remove(ppi)

    # Mean PPI
    mean_ppi = round(sum(ppi_data) / len(ppi_data))
    mean_ppi = int(mean_ppi)

    if mean_ppi == 0:
        print("Mean PPI is zero, cannot compute HRV metrics.")
        return {
            "Mean_PPI": 0,
            "Mean_HR": 0,
            "SDNN": 0,
            "RMSSD": 0
        }
    
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

