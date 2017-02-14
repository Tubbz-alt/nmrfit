import NMRfit as nmrft
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore")


def run_fit(exp, method='auto'):
    ID = os.path.basename(exp)
    sample = ID.split('_')[1]
    trial = ID.split('_')[-2]
    end = ID.split('_')[-1].split('.')[0]
    print(ID)

    c = ['id', 'sample', 'method', 'error', 'fraction',
         'theta', 'GLratio', 'yoff']
    for i in range(1, 7):
        c.extend(['s' + str(i), 'loc' + str(i), 'a' + str(i)])

    # read in data
    data = nmrft.varian_process(os.path.join(exp, 'fid'), os.path.join(exp, 'procpar'))

    # bound the data
    if sample == '4b':
        if int(trial) in [3, 4, 5]:
            data.select_bounds(low=3.2, high=3.6)
        else:
            data.select_bounds(low=3.25, high=3.6)
    elif sample == '4d':
        if end == '072316':
            data.select_bounds(low=3.23, high=3.6)
        else:
            data.select_bounds(low=3.25, high=3.6)
    else:

        data.select_bounds(low=3.2, high=3.6)

    # select peaks and satellites
    data.select_peaks(method=method, n=6, plot=False, thresh=0.002)

    # generate bounds and initial conditions
    x0, bounds = data.generate_initial_conditions()

    # fit data
    fit = nmrft.FitUtility(data, x0, method='Powell')

    # generate result
    res = fit.generate_result(scale=1)

    # row = [ID, sample, 'Powell', res.error, res.area_fraction]
    # if len(row) + len(res.params) == len(c):
    #     row.extend(res.params)
    # else:
    #     print('Powell fit error...')
    #     row.extend(['NA' for i in range(len(c) - len(row))])

    # plt.close()
    # plt.plot(fit.data.w, fit.data.V, linewidth=2, alpha=0.5)
    # plt.plot(fit.result.w, fit.result.V, linewidth=2, alpha=0.5)
    # plt.xlabel('Frequency')
    # plt.ylabel('Amplitude')
    # plt.savefig('./results/%s_powell.png' % ID)

    # Now we will pass global results onto TNC
    x0[1:3] = res.params[1:3]

    # fit data
    fit = nmrft.FitUtility(data, x0, method='TNC', bounds=bounds, options={'maxCGit': 1000, 'maxiter': 1000})

    # generate result
    res = fit.generate_result(scale=1)

    row = [ID, sample, 'TNC', res.error, res.area_fraction]
    if len(row) + len(res.params) == len(c):
        row.extend(res.params)
    else:
        print('TNC fit error...')
        row.extend(['NA' for i in range(len(c) - len(row))])

    # plt.close()
    # plt.plot(fit.data.w, fit.data.V, linewidth=2, alpha=0.5)
    # plt.plot(fit.result.w, fit.result.V, linewidth=2, alpha=0.5)
    # plt.xlabel('Frequency')
    # plt.ylabel('Amplitude')
    # plt.savefig('./results/%s_tnc.png' % ID, bbox_inches='tight')
    # plt.close()

    return row


if __name__ == '__main__':

    # auto = pd.read_csv('./results/auto_cases.csv')['id'].values
    # manual = pd.read_csv('./results/problematic.csv')['id'].values

    # input directory
    inDir = "./Data/blindedData/"
    experiments = glob.glob(os.path.join(inDir, '*.fid'))

    l = []
    # for fn in auto:
    #     exp = os.path.join(inDir, fn)
    #     l.append(run_fit(exp, method='auto'))

    # for fn in manual:
    #     exp = os.path.join(inDir, fn)
    #     l.append(run_fit(exp, method='auto'))

    for exp in experiments:
        l.append(run_fit(exp, method='auto'))

    # construct column labels
    c = ['id', 'sample', 'method', 'error', 'fraction',
         'theta', 'GLratio', 'yoff']
    for i in range(1, 7):
        c.extend(['s' + str(i), 'loc' + str(i), 'a' + str(i)])

    # build dataframe
    df = pd.DataFrame(l, columns=c)
    df.to_csv('./results/results.csv', index=False)
