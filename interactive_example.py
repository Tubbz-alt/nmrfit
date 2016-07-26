import NMRfit as nmrft
import os


inDir = "./Data/organophosphate/dc-919V_cdcl3_kilimanjaro_25c_1d_1H_1_031916.fid"
w, u, v, theta0 = nmrft.varian_process(os.path.join(inDir, 'fid'), os.path.join(inDir, 'procpar'))

# create data object
data = nmrft.Data(w, u, v, theta0)

# bound the data
data.select_bounds(low=3.2, high=3.6)

# interactively select peaks and satellites
p = data.select_peaks(2)
s = data.select_satellites(4)

# weights across ROIs
weights = [['all', 1.0],
           ['all', 1.0],
           [s[0].bounds, p[0].height / s[0].height],
           [s[1].bounds, p[0].height / s[1].height],
           [s[2].bounds, p[0].height / s[2].height],
           [s[3].bounds, p[0].height / s[3].height]]

# initial conditions of the form [theta, r, yOff, sigma_n, mu_n, a_n,...]
x0 = [0, 0.1, 0,                                  # shared params
      p[0].width / 10, p[0].loc, p[0].area,       # p1 init
      p[1].width / 10, p[1].loc, p[1].area,       # p2 init
      p[1].width / 10, s[0].loc, s[0].area,       # s1 init
      p[1].width / 10, s[1].loc, s[1].area,       # s2 init
      p[1].width / 10, s[2].loc, s[2].area,       # s3 init
      p[1].width / 10, s[3].loc, s[3].area]       # s4 init

# fit data
fit = nmrft.FitUtility(data, x0, weights=weights)

# generate result
res = fit.generate_result(scale=1)

# plot summary
fit.summary_plot(p, s)
