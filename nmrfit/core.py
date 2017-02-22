import numpy as np
import nmrglue as ng
import matplotlib.pyplot as plt
import pyswarm
import multiprocessing as mp

from . import proc_autophase
from . import equations
from . import containers


class FitUtility:
    """
    Interface used to perform a fit of the data.

    Attributes
    ----------
    data : instance of Data class
        Container for ndarrays relevant to the fitting process (w, u, v, V, I).
    result : instance of Result class
        Container for ndarrays (w, u, v, V, I) of the fit result.
    lower, upper : list of floats
            Min, max bounds for each parameter in the optimization.
    expon : float
        Raise relative weighting to this power.
    fit_im : bool
        Specify whether the imaginary part of the spectrum will be fit. Computationally expensive.
    options : dict, optional
        Used to pass additional options to the minimizer.
    weights : ndarray
        Array giving frequency-dependent weighting of error.

    """

    def __init__(self, data, lower, upper, expon=0.5, fit_im=False, options=None):
        """
        FitUtility constructor.

        Parameters
        ----------
        data : instance of Data class
            Container for ndarrays relevant to the fitting process (w, u, v, V, I).
        lower, upper : list of floats
            Min, max bounds for each parameter in the optimization.
        expon : float
            Raise relative weighting to this power.
        fit_im : bool
            Specify whether the imaginary part of the spectrum will be fit. Computationally expensive.
        options : dict, optional
            Used to pass additional options to the minimizer.

        """
        self.result = containers.Result()
        self.data = data

        # bounds
        self.lower = lower
        self.upper = upper

        # whether to fit imaginary
        self.fit_im = fit_im

        self.expon = expon

        # any additional options for the minimization step
        self.options = options

        # call to the fit method
        self.fit()

    def fit(self):
        """
        Fit a number of Voigt functions to the input data by objective function minimization.  By default, only the real
        component of the data is used when performing the fit.  The imaginary data can be used, but at a severe performance
        penalty (often with little to no gains in goodness of fit).

        """
        self.weights = self._compute_weights()

        # call to the minimization function
        xopt, fopt = pyswarm.pso(equations.objective, self.lower, self.upper, args=(self.data.w, self.data.u, self.data.v, self.weights, self.fit_im),
                                 swarmsize=204,
                                 maxiter=2000,
                                 omega=-0.2134,
                                 phip=-0.3344,
                                 phig=2.3259,
                                 processes=mp.cpu_count() - 1)

        # store the fit parameters and error in the result object
        self.result.params = xopt
        self.result.error = fopt
        self.result.area_fraction = self._calculate_area_fraction()

    def _compute_weights(self):
        """
        Smoothly weights each peak based on its height relative to the largest peak.

        Returns
        -------
        weights : ndarray
            Array giving frequency-dependent weighting of error.

        """
        lIdx = np.zeros(len(self.data.peaks), dtype=np.int)
        rIdx = np.zeros(len(self.data.peaks), dtype=np.int)
        maxabs = np.zeros(len(self.data.peaks))

        for i, p in enumerate(self.data.peaks):
            lIdx[i] = np.argmin(np.abs(self.data.w - p.bounds[0]))
            rIdx[i] = np.argmin(np.abs(self.data.w - p.bounds[1]))
            if lIdx[i] > rIdx[i]:
                temp = lIdx[i]
                lIdx[i] = rIdx[i]
                rIdx[i] = temp

            maxabs[i] = np.abs(p.height)

        biggest = np.amax(maxabs)

        defaultweight = 0.1
        weights = np.ones(len(self.data.w)) * defaultweight

        for i in range(len(self.data.peaks)):
            weights[lIdx[i]:rIdx[i] + 1] = np.power(biggest / maxabs[i], self.expon)

        weights = equations.laplace1d(weights)
        return weights

    def generate_result(self, scale=10):
        """
        Uses the output of the fit method to generate results.

        Parameters
        ----------
        scale : float, optional
            Upsample the resolution by this factor when calculating the fits.

        """
        if scale == 1.0:
            # just use w vector as is
            w = self.data.w
        else:
            # upsample the w vector for plotting
            w = np.linspace(self.data.w.min(), self.data.w.max(), int(scale * self.data.w.shape[0]))

        # initialize arrays for the fit of V and I
        V_fit = np.zeros_like(w)
        I_fit = np.zeros_like(w)

        # extract global params from result object
        theta, r, yoff = self.result.params[:3]
        res = self.result.params[3:]

        # transform u and v to get V and I for the data
        V_data = self.data.u * np.cos(theta) - self.data.v * np.sin(theta)
        I_data = self.data.u * np.sin(theta) + self.data.v * np.cos(theta)

        # iteratively add the contribution of each peak to the fits for V and I
        for i in range(0, len(res), 3):
            width = res[i]
            loc = res[i + 1]
            a = res[i + 2]

            V_fit = V_fit + equations.voigt(w, r, yoff, width, loc, a)
            I_fit = I_fit + equations.kk_relation_parallel(w, r, yoff, width, loc, a)

        # transform the fits for V and I to get fits for u and v
        u_fit = V_fit * np.cos(theta) + I_fit * np.sin(theta)
        v_fit = -V_fit * np.sin(theta) + I_fit * np.cos(theta)

        # populate the result object
        self.result.u = u_fit
        self.result.v = v_fit
        self.result.V = V_fit
        self.result.I = I_fit
        self.result.w = w

        # update the data object
        self.data.V = V_data
        self.data.I = I_data

    def _calculate_area_fraction(self):
        """
        Calculates the relative fraction of the satellite peaks to the total peak area from the fit.

        """
        areas = np.array([self.result.params[i] for i in range(5, len(self.result.params), 3)])
        m = np.mean(areas)
        peaks = areas[areas >= m].sum()
        sats = areas[areas < m].sum()

        area_fraction = (sats / (peaks + sats))

        # calculate area fraction
        return area_fraction

    def _summary_plot(self):
        """
        Generates a summary plot of the calculated fit alongside the input data.

        """
        peaks, satellites = self.data.peaks.split()

        peakBounds = []
        for p in peaks:
            low, high = p.bounds
            peakBounds.append(low)
            peakBounds.append(high)

        peakRange = [min(peakBounds) - 0.005, max(peakBounds) + 0.005]

        set1Bounds = []
        set2Bounds = []
        satHeights = []
        for s in satellites:
            low, high = s.bounds
            satHeights.append(s.height)
            if high < peakRange[0]:
                set1Bounds.append(low)
                set1Bounds.append(high)
            else:
                set2Bounds.append(low)
                set2Bounds.append(high)

        set1Range = [min(set1Bounds) - 0.02, max(set1Bounds) + 0.02]
        set2Range = [min(set2Bounds) - 0.02, max(set2Bounds) + 0.02]
        ht = max(satHeights)

        # set up figures
        fig_re = plt.figure(1, figsize=(16, 12))
        ax1_re = plt.subplot(211)
        ax2_re = plt.subplot(234)
        ax3_re = plt.subplot(235)
        ax4_re = plt.subplot(236)

        # plot everything
        ax1_re.plot(self.result.w, self.result.V, linewidth=2, alpha=0.5, color='r', label='Area Fraction: %03f' % self.result.area_fraction)
        ax1_re.plot(self.data.w, self.data.V, linewidth=2, alpha=0.5, color='b', label='Error: %03f' % self.result.error)
        ax1_re.legend(loc='upper right')

        # plot left sats
        ax2_re.plot(self.data.w, self.data.V, linewidth=2, alpha=0.5, color='b')
        ax2_re.plot(self.result.w, self.result.V, linewidth=2, alpha=0.5, color='r')
        ax2_re.set_ylim((0, ht * 1.5))
        ax2_re.set_xlim(set1Range)

        # plot main peaks
        ax3_re.plot(self.data.w, self.data.V, linewidth=2, alpha=0.5, color='b')
        ax3_re.plot(self.result.w, self.result.V, linewidth=2, alpha=0.5, color='r')
        ax3_re.set_xlim(peakRange)

        # plot right satellites
        ax4_re.plot(self.data.w, self.data.V, linewidth=2, alpha=0.5, color='b')
        ax4_re.plot(self.result.w, self.result.V, linewidth=2, alpha=0.5, color='r')
        ax4_re.set_ylim((0, ht * 1.5))
        ax4_re.set_xlim(set2Range)

        # # imag
        # fig_im = plt.figure(2)
        # ax1_im = plt.subplot(211)
        # ax2_im = plt.subplot(234)
        # ax3_im = plt.subplot(235)
        # ax4_im = plt.subplot(236)

        # # plot everything
        # ax1_im.plot(self.data.w, self.data.I, linewidth=2, alpha=0.5, color='b', label='Data')
        # ax1_im.plot(self.result.w, self.result.I, linewidth=2, alpha=0.5, color='r', label='Fit')

        # # plot left sats
        # ax2_im.plot(self.data.w, self.data.I, linewidth=2, alpha=0.5, color='b')
        # ax2_im.plot(self.result.w, self.result.I, linewidth=2, alpha=0.5, color='r')
        # ax2_im.set_xlim(set1Range)

        # # plot main peaks
        # ax3_im.plot(self.data.w, self.data.I, linewidth=2, alpha=0.5, color='b')
        # ax3_im.plot(self.result.w, self.result.I, linewidth=2, alpha=0.5, color='r')
        # ax3_im.set_xlim(peakRange)

        # # plot right satellites
        # ax4_im.plot(self.data.w, self.data.I, linewidth=2, alpha=0.5, color='b')
        # ax4_im.plot(self.result.w, self.result.I, linewidth=2, alpha=0.5, color='r')
        # ax4_im.set_xlim(set2Range)

        # display
        fig_re.tight_layout()
        plt.show()

    def _print_summary(self):
        """
        Generates and prints a summary of the fitting process.

        """
        res = np.array(self.result.params).reshape((-1, 3))
        res_globals = res[0, :]
        res = res[1:, :]

        print()
        print('CONVERGED PARAMETER VALUES:')
        print('---------------------------')
        print('Global parameters')
        print(res_globals)
        print('Peak parameters')
        for i in range(res.shape[0]):
            print(res[i, :])

        print("Error:  ", self.result.error)
        print("Area fraction:  ", self.result.area_fraction)

    def summary(self, plot=True):
        """
        Convenience function to print a summary as well as display summary plots.

        Parameters
        ----------
        plot : bool, optional
            Signals whether a plot of the resulting fit will be generated.

        """
        self._print_summary()
        if plot is True:
            self._summary_plot()


def load(fidfile, procfile):
    """
    Loads NMR spectra data from relevant input files.

    Parameters
    ----------
    fidfile : string
        Path to the fid file.
    procfile : string
        Path to the procpar file.

    Returns
    -------
    result : instance of Data class
        Container for ndarrays relevant to the fitting process (w, u, v, V, I).

    """
    dic, data = ng.varian.read_fid(fidfile)
    procs = ng.varian.read_procpar(procfile)

    offset = [float(i) for i in procs['tof']['values']][0]
    magfreq = [float(i) for i in procs['sfrq']['values']][0]
    rangeHz = [float(i) for i in procs['sw']['values']][0]

    rangeppm = rangeHz / magfreq
    offsetppm = offset / magfreq

    w = np.linspace(rangeppm - offsetppm, -offsetppm, data.size)

    # Fourier transform
    data = ng.proc_base.fft(data)
    data = data / np.max(data)

    # phase correct
    p0, p1 = proc_autophase.approximate_phase(data, 'acme')

    u = data[0, :].real
    v = data[0, :].imag

    result = containers.Data(w[::-1], u[::-1], v[::-1], p0, p1)
    return result
