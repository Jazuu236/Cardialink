# meanPPI from hr
def meanPPI_calculator(hr_list):
    ppi_values = [60000 / hr for hr in hr_list]
    return sum(ppi_values) / len(ppi_values)

# meanHr form PPIa
def meanHR_calculator(meanPPI):
    return 60000 / mean_ppi

# SDNN calculator
def SDNN_calculator(ppi_list):
    mean_ppi = sum(ppi_list) / len(ppi_list)
    return ((sum((x-mean_ppi) ** 2 for x in ppi_list) / (len(ppi_list) - 1)) ** 0.5)

# RMSSD calculator
def RMSSD_calculator(ppi_list):
    diffs = [(ppi_list[i+1] - ppi_list[i]) ** 2 for i in range(len(ppi_list)-1)]
    return (sum(diffs) / len(diffs) ** 0.5)
                 
# HR data
hr_data = []

# Diffrent values
ppi_values = [60000 / hr for hr in hr_data]
mean_ppi = meanPPI_calculator(hr_data)
mean_hr = meanHR_calculator(mean_ppi)
sdnn = SDNN_calculator(ppi_values)
rmssd = RMSSD_calculator(ppi_values)


print("Mean PPI:", round(mean_ppi), "ms")
print("Mean HR:", round(mean_hr), "bpm")
print("SDNN:", round(sdnn), "ms")
print("RMSSD:", round(rmssd), "ms")
