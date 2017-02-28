"""nmrfit reads the output from an NMR spectroscopy experiment and,
through a number of intuitive API calls, produces a least-squares
fit of Voigt-function approximations via particle swarm optimization.
Fitted peaks can then be used to perform quantitative NMR analysis,
including isotope ratio approximation."""

from ._core import *

__author__ = 'Sean M. Colby'
__version__ = '0.1'
