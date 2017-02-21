import numpy as np
from .utility import AutoPeakSelector
from .utility import PeakSelector
from .utility import BoundsSelector
from .utility import Peaks
from .proc_autophase import ps2


class Result:
    """
    Used to store results of the fit.  Similar to the Data class, but without the methods.

    Attributes
    ----------
    w : ndarray
        Array of frequency data.
    u, v : ndarray
        Arrays of the real and imaginary components of the frequency response.
    V, I : ndarray
        Arrays of the phase corrected real and imaginary components of the frequency response.
    params : ndarray
        Solution vector.
    error : float
        Weighted sum of squared error between the data and fit.

    """


class Data:
    """
    Stores data relevant to the NMRfit module and provides methods to interface with a number
    of utility classes.

    Attributes
    ----------
    w : ndarray
        Array of frequency data.
    u, v : ndarray
        Arrays of the real and imaginary components of the frequency response.
    V, I : ndarray
        Arrays of the phase corrected real and imaginary components of the frequency response.
    theta : float
        Phase correction value in radians.
    peaks : list of peak instances
        List containing instances of Peak objects, which contain information about each peak.
    roibounds : list of 2 tuples
        Frequency bounds of each peak.
    area_fraction : float
        Area fraction of satellite peaks.

    """

    def __init__(self, w, u, v, p0, p1):
        """
        Constructor for the Data class.

        Parameters
        ----------
        w : ndarray
            Array of frequency data.
        u, v : ndarray
            Arrays of the real and imaginary components of the frequency response.
        p0, p1 : float
            Estimate of zeroth and first order phase in radians.

        """
        self.w = w
        self.u = u
        self.v = v

        self.p0 = p0
        self.p1 = p1

    def shift_phase(self, p0, p1):
        """
        Phase shift u and v by theta to generate V and I.

        Parameters
        ----------
        p0,, p1 : float
            Phase correction in radians.

        """
        # calculate V and I from u, v, and theta
        self.V, self.I = ps2(self.u, self.v, p0, p1)

    def brute_phase(self, step=np.pi / 360):
        bestTheta = 0
        bestError = np.inf
        for theta in np.arange(-np.pi, np.pi, step):
            self.V, self.I = ps2(self.u, self.v, theta, 0)
            error = (self.V[0] - self.V[-1])**2
            if error < bestError:
                bestError = error
                bestTheta = theta

        self.V, self.I = ps2(self.u, self.v, bestTheta, 0)
        self.p0 = bestTheta
        return bestTheta

    def select_bounds(self, low=None, high=None):
        """
        Method to interface with the utility class BoundsSelector.  If low and high are supplied, the interactive
        aspect will be overridden.

        Parameters
        ----------
        low : float, optional
            Lower bound.
        high : float, optional
            Upper bound.

        """
        if low is not None and high is not None:
            bs = BoundsSelector(self.w, self.u, self.v, supress=True)
            self.w, self.u, self.v = bs.apply_bounds(low=low, high=high)
        else:
            bs = BoundsSelector(self.w, self.u, self.v)
            self.w, self.u, self.v = bs.apply_bounds()

        # self.shift_phase(self.p0, self.p1)

    def select_peaks(self, method='auto', n=None, thresh=0.0, window=0.02, plot=False):
        """
        Method to interface with the utility class PeakSelector.  Will open an interactive utility used to select
        peaks n times.

        Parameters
        ----------
        method : str, optional
            Flag to determine whether peaks will be selected automatically ('auto') or manually ('manual')
        n : int
            Number of peaks to select.  Only required if 'manual' is selected.
        thresh : float, optional
            Threshold for peak detection. Only used if 'auto' is selected.
        window : float, optional
            Window for local non-maximum supression. Only used if 'auto' is selected.

        Returns
        -------
        peaks : list of Peak instances
            List containing instances of Peak objects, which contain information about each peak.

        """
        if method.lower() == 'manual':
            if isinstance(n, int) and n > 0:
                ps = PeakSelector(self.w, self.V, n)
            else:
                raise ValueError("Number of peaks must be specified when using 'manual' flag")

        elif method.lower() == 'auto':
            ps = AutoPeakSelector(self.w, self.V, thresh, window)
            ps.find_peaks()

        else:
            raise ValueError("Method must be 'auto' or 'manual'.")

        if plot is True:
            ps.plot()

        self.peaks = ps.peaks

        self.roibounds = []
        for p in self.peaks:
            self.roibounds.append(p.bounds)

        return self.peaks

    def generate_initial_conditions(self):
        """
        Uses initial theta approximation as well as initial per-peak parameters (width, location, area)
        to construct a set of parameter bounds.

        Returns
        -------
        lower, upper : list of 2-tuples
            Min, max bounds for each parameter in optimization.

        """
        # upper = [np.pi, 1.0, 0.01]
        # lower = [-np.pi, 0.0, -0.01]

        upper = [self.p0 + 0.01, 1.0, 0.01]
        lower = [self.p0 - 0.01, 0.0, -0.01]

        for p in self.peaks:
            lower.extend([p.width * 0.5, p.loc - 0.1 * (p.loc - p.bounds[0]), p.area * 0.5])
            upper.extend([p.width * 1.5, p.loc - 0.1 * (p.loc - p.bounds[1]), p.area * 1.5])

        return lower, upper

    def approximate_areas(self):
        """
        Extracts the area attribute from each Peak instance and returns as a list.

        Returns
        -------
        areas : list of floats
            A list containing the peak area of each Peak instance.

        """
        areas = []
        for p in self.peaks:
            areas.append(p.area)
        return areas

    def approximate_area_fraction(self):
        """
        Calculates the relative fraction of the satellite peaks to the total peak area from the data.

        Returns
        -------
        area_fraction : float
            Area fraction of satellite peaks.

        """
        areas = np.array(self.approximate_areas())

        m = np.mean(areas)
        peaks = areas[areas >= m].sum()
        sats = areas[areas < m].sum()

        area_fraction = sats / (peaks + sats)

        return area_fraction
