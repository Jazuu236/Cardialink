# HRV analysis
def hrv_analysis(hr_list):
    ppi_list = [60000 / hr for hr in hr_list]
    
    # Mean PPI
    mean_ppi = round(sum(ppi_list) / len(ppi_list))
    mean_ppi = int(mean_ppi)
    
    # Mean HR
    mean_hr = int(round(60000 / mean_ppi))
    
    # SDNN
    sdnn = round((sum((x - mean_ppi) ** 2 for x in ppi_list) / (len(ppi_list) - 1)) ** 0.5)
    
    # RMSSD
    diffs = [(ppi_list[i+1] - ppi_list[i]) ** 2 for i in range(len(ppi_list)-1)]
    rmssd = round((sum(diffs) / len(diffs)) ** 0.5)

    return {
        "mean_ppi": mean_ppi,
        "mean_hr": mean_hr,
        "sdnn": sdnn,
        "rmssd": rmssd
    }
