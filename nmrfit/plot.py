import matplotlib.pyplot as plt


def individual_contributions(data, result, component='real'):
    """
    Generates a summary plot of the calculated fit alongside the input data.

    Parameters
    ----------
    data : instance of Data class
        Container for ndarrays relevant to the fitting process (w, u, v, V, I).
    result : instance of Result class
        Container for ndarrays (w, u, v, V, I) of the fit result.
    component : string, optional
        Flag to specify the real or imaginary component will be plotted.

    """
    x_data = data.w
    x_res = result.w
    if component.lower() == 'real':
        y_data = data.V
        y_res = result.real_contribs
    elif component.lower() == 'imag':
        y_data = data.I
        y_res = result.imag_contribs
    else:
        raise ValueError("Valid options are 'real' and 'imag'.")

    plt.plot(x_data, y_data, color='black')
    for peak in y_res:
        plt.plot(x_res, peak)

    plt.xlabel('Frequency')
    plt.ylabel('Amplitude')
    plt.show()


def isotope_ratio(data, result):
        """
        Generates a summary plot of the calculated fit alongside the input data.

        Parameters
        ----------
        data : instance of Data class
            Container for ndarrays relevant to the fitting process (w, u, v, V, I).
        result : instance of Result class
            Container for ndarrays (w, u, v, V, I) of the fit result.

        """
        peaks, satellites = data.peaks.split()

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
        ax1_re.plot(result.w, result.V, linewidth=2, alpha=0.5, color='r', label='Area Fraction: %03f' % result.area_fraction)
        ax1_re.plot(data.w, data.V, linewidth=2, alpha=0.5, color='b', label='Error: %03f' % result.error)
        ax1_re.legend(loc='upper right')

        # plot left sats
        ax2_re.plot(data.w, data.V, linewidth=2, alpha=0.5, color='b')
        ax2_re.plot(result.w, result.V, linewidth=2, alpha=0.5, color='r')
        ax2_re.set_ylim((0, ht * 1.5))
        ax2_re.set_xlim(set1Range)

        # plot main peaks
        ax3_re.plot(data.w, data.V, linewidth=2, alpha=0.5, color='b')
        ax3_re.plot(result.w, result.V, linewidth=2, alpha=0.5, color='r')
        ax3_re.set_xlim(peakRange)

        # plot right satellites
        ax4_re.plot(data.w, data.V, linewidth=2, alpha=0.5, color='b')
        ax4_re.plot(result.w, result.V, linewidth=2, alpha=0.5, color='r')
        ax4_re.set_ylim((0, ht * 1.5))
        ax4_re.set_xlim(set2Range)

        # # imag
        # fig_im = plt.figure(2)
        # ax1_im = plt.subplot(211)
        # ax2_im = plt.subplot(234)
        # ax3_im = plt.subplot(235)
        # ax4_im = plt.subplot(236)

        # # plot everything
        # ax1_im.plot(data.w, data.I, linewidth=2, alpha=0.5, color='b', label='data')
        # ax1_im.plot(result.w, result.I, linewidth=2, alpha=0.5, color='r', label='Fit')

        # # plot left sats
        # ax2_im.plot(data.w, data.I, linewidth=2, alpha=0.5, color='b')
        # ax2_im.plot(result.w, result.I, linewidth=2, alpha=0.5, color='r')
        # ax2_im.set_xlim(set1Range)

        # # plot main peaks
        # ax3_im.plot(data.w, data.I, linewidth=2, alpha=0.5, color='b')
        # ax3_im.plot(result.w, result.I, linewidth=2, alpha=0.5, color='r')
        # ax3_im.set_xlim(peakRange)

        # # plot right satellites
        # ax4_im.plot(data.w, data.I, linewidth=2, alpha=0.5, color='b')
        # ax4_im.plot(result.w, result.I, linewidth=2, alpha=0.5, color='r')
        # ax4_im.set_xlim(set2Range)

        # display
        fig_re.tight_layout()
        plt.show()