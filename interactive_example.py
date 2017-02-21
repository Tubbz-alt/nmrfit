import NMRfit as nmrft
import os
import matplotlib.pyplot as plt
import numpy as np


# input directory
inDir = "./data/toluene/toluene2_cdcl3_long2_070115.fid"

# read in data
data = nmrft.varian_process(os.path.join(inDir, 'fid'), os.path.join(inDir, 'procpar'))

# bound the data
data.select_bounds(low=3.30, high=3.7)

data.shift_phase(method='auto')

# select peaks and satellites
peaks = data.select_peaks(method='auto', n=3, plot=False)

# generate bounds and initial conditions
lb, ub = data.generate_initial_conditions()

# fit data
fit = nmrft.FitUtility(data, lb, ub)

# generate result
fit.generate_result(scale=10)

# summary
fit.summary()
