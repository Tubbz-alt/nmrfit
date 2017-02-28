import numpy as _np
import nmrglue as _ng

from . import _proc_autophase
from . import _containers
from . import _utility
from . import plot


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
    dic, data = _ng.varian.read_fid(fidfile)
    procs = _ng.varian.read_procpar(procfile)

    offset = [float(i) for i in procs['tof']['values']][0]
    magfreq = [float(i) for i in procs['sfrq']['values']][0]
    rangeHz = [float(i) for i in procs['sw']['values']][0]

    rangeppm = rangeHz / magfreq
    offsetppm = offset / magfreq

    w = _np.linspace(rangeppm - offsetppm, -offsetppm, data.size)

    # Fourier transform
    data = _ng.proc_base.fft(data)
    data = data / _np.max(data)

    # phase correct
    p0, p1 = _proc_autophase.approximate_phase(data, 'acme')

    u = data[0, :].real
    v = data[0, :].imag

    result = _containers.Data(w[::-1], u[::-1], v[::-1], p0, p1)
    return result


def fit(data, lower, upper, expon=0.5, fit_im=False, summary=True, options={}):
    '''
    Perform a fit of NMR spectroscopy data.

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
    summary : bool
        Flag to display a summary of the fit.
    options : dict, optional
        Used to pass additional options to the minimizer.

    Returns
    -------
    f : FitUtility
        Object containing result of the fit.

    '''
    f = _utility.FitUtility(data, lower, upper, expon, fit_im, summary, options)
    f.fit()
    return f
