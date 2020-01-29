``nmrfit``
==========
``nmrfit`` reads the output from an NMR spectroscopy experiment and, through a number of intuitive API calls, produces a least-squares fit of  Voigt-function approximations via particle swarm optimization ([``PySwarm``](https://github.com/tisimst/pyswarm)). Fitted peaks can then be used to perform quantitative NMR analysis, including isotope ratio approximation.

Installation
------------
``nmrfit`` will soon be available through the Python Package Index ([PyPI](https://pypi.python.org/pypi)).  Simply run ``pip install nmrfit`` to install ``nmrfit`` and all required dependencies.  Until then, please install by running

```bash
pip install git+https://github.com/pnnl/nmrfit.git
```

NOTE: the latest version of PySwarm is required, but is not available through PyPI.  Manually install as follows:

```bash
pip install git+https://github.com/tisimst/pyswarm.git
```

Getting Started
---------------
To read input data, ``nmrfit`` relies on the [``nmrglue``](https://www.nmrglue.com/ "nmrglue homepage") package.  Real and imaginary spectrum components are stored in a custom class, allowing data preprocessing operations to naturally extend from the object as methods.  The data is then processed by Python script using the ``nmrfit`` API.

```python
# import the module
import nmrfit

# read in data
data = nmrfit.load('fid', 'propcar')
```
In many cases, the signal of interest comprises only a subsection of the captured spectrum.  To restrict the fitting algorithm to only the pertinent part of the signal, the method ``get_bounds()`` is used to bound the data with respect to frequency.  The lower and upper bounds may be passed as arguments, or no arguments may be passed to prompt the user to interactively select the bounds by clicking twice on a displayed plot of the data.  To prepare for subsequent steps, nmrglue package is again used to perform an initial, approximate phase correction (initial phase correction is later refined by the fitting process).

```python
# bound the data interactively
data.select_bounds()

# alternatively, pass the bounds
data.select_bounds(low=3.23, high=3.60)

# phase correction
data.shift_phase(method='auto')
```

In order to parameter bounds, approximate initial parameters must be extracted from the data.  This is achieved by determining the total number of peaks, finding each peak's center, width, and area, and then using this information to construct solution bounds and weight vectors.  The user may perform this manually--clicking twice per peak to define peak bounds, whereafter peak attributes are calculated--or automatically--wherein a peak-detection algorithm is run--through the method ``select_peaks()``.  In either case, the plot flag may be enabled to visualize the results of the peak selection process.  Note that in the manual case, a flag specifiying the number of peaks must be passed.

```python
# select peaks automatically
data.select_peaks(method='auto', plot=True)

# select peaks manually
data.select_peaks(method='manual', n=6, plot=True)
```

The ``generate_solution_bounds()`` method is then used to create upper and lower bounds for the fit by least-squares minimization.  Each set of bounds (lower, upper) contains 3 global parameters (phase shift, Gaussian-Lorentzian ratio, and y-offset) and 3 parameters per peak (width, center, and area).  These values are used to construct area-parameterized Voigt-body approximations for each peak.  

```python
# generate the solution bounds
lb, ub = data.generate_solution_bounds()
```

``nmrfit.fit()``  is then called, requiring a ``Data`` object and solution bounds to perform a fit via minimization.  Each time the optimizer calls the objective function, the target data is phase-shifted by theta, Voigt-body approximations are generated for each peak and summed to create a fit of the entire signal, and a residual is calculated between the fit and the data.  ``nmrfit.fit()`` returns a ``FitUtility`` object.

Once the optimizer converges, the ``FitUtility`` method ``generate_result()`` generates the final fit from the solution vector. Residual error, the fit parameter vector, and real and imaginary components of the phase-corrected and out-of-phase fits are stored in the ``FitUtility`` object.  The ``scale`` flag may be adjusted to upsample the resulting fit by a constant factor.  This is useful when high-resolution output is desired.

```python
# perform the fit
fit = nmrfit.fit(data, lb, ub)

# generate results
fit.generate_result(scale=1)
```

Lastly, use the ``plot`` module to generate publication-ready plots of your results, e.g.:

```python
nmrfit.plot.residual(data, fit)
```

Citing nmrfit
-------------
Citation coming soon! We ask that you reference the citation that will be posted here if you use software.

Disclaimer
----------
This material was prepared as an account of work sponsored by an agency of the United States Government. Neither the United States Government nor the United States Department of Energy, nor Battelle, nor any of their employees, nor any jurisdiction or organization that has cooperated in the development of these materials, makes any warranty, express or implied, or assumes any legal liability or responsibility for the accuracy, completeness, or usefulness or any information, apparatus, product, software, or process disclosed, or represents that its use would not infringe privately owned rights.

Reference herein to any specific commercial product, process, or service by trade name, trademark, manufacturer, or otherwise does not necessarily constitute or imply its endorsement, recommendation, or favoring by the United States Government or any agency thereof, or Battelle Memorial Institute. The views and opinions of authors expressed herein do not necessarily state or reflect those of the United States Government or any agency thereof.

PACIFIC NORTHWEST NATIONAL LABORATORY operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY under Contract DE-AC05-76RL01830
