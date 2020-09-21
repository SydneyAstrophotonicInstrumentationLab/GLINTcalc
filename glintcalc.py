"""
Methods to use for the GLINT signal calculator
Run from run_glintcalc.py
"""
import numpy as np
from numpy.random import randn
import matplotlib.pyplot as plt

class glintcalc:
    def __init__(self, wavelength=1.6):
        self.nullsamps = None
        self.wavelength = wavelength


    def get_null_vals_MC(self, deltaphi_sig, deltaI_sig, deltaphi_mu=0, deltaI_mu = 0,
                         num_samps=100000, show_plot=False, hist_bins=100):
        # Let total flux I1+I2 = 1
        # Assume N+ >> N-, deltaphi <<1 and deltaI << 1, so can approximate:
        # (See Hanot+ 2011, Norris+ 2020)
        wavelength = self.wavelength
        deltaphi_sig_rad = deltaphi_sig/wavelength * 2 * np.pi
        dIsamps = randn(num_samps) * deltaI_sig + deltaI_mu
        dphisamps = randn(num_samps) * deltaphi_sig_rad + deltaphi_mu
        self.nullsamps = 0.25 * (dIsamps**2 + dphisamps**2)
        self.av_null = np.mean(self.nullsamps)

        if show_plot:
            plt.figure(1)
            plt.clf()
            plt.hist(self.nullsamps, hist_bins, density=True)
            plt.xlabel('Null depth')
            plt.ylabel('Frequency')

        return self.av_null


    def plot_null_dphi(self, deltaI_sig, max_dphi=None, npoints=100):
        if max_dphi is None:
            max_dphi = self.wavelength/10
        dphis = np.linspace(0, max_dphi, npoints)
        all_nulls = np.zeros(npoints)
        for k in range(npoints):
            all_nulls[k] = self.get_null_vals_MC(dphis[k], deltaI_sig)
        plt.figure(2)
        plt.clf()
        plt.plot(dphis,all_nulls)
        plt.xlabel('dphi sigma (microns)')
        plt.ylabel('Average null')


    def get_chromatic_null(self, deltaphi_sig, deltaI_sig, bandwidth, npoints = 50, show_plot=False):
        # Make the assumption that null is purely chromatic, i.e. behaves like free space optics
        all_wl_offsets = np.linspace(-bandwidth/2, bandwidth/2, npoints)

        all_nulls = np.zeros(npoints)
        for k in range(npoints):
            all_nulls[k] = self.get_null_vals_MC(deltaphi_sig, deltaI_sig, deltaphi_mu=all_wl_offsets[k],
                                                 num_samps=1000000)
        chromatic_null = np.mean(all_nulls)

        if show_plot:
            plt.figure(3)
            plt.clf()
            plt.plot(all_wl_offsets+self.wavelength, all_nulls)
            plt.xlabel('Wavelength (microns)')
            plt.ylabel('Average null_depth')
            plt.tight_layout()

        return chromatic_null


    def get_snr(self, photon_flux, bandwidth, contrast, null_depth, throughput=1, pupil_area=50,
                             int_time=1, read_noise=1, QE=1, num_pix=1):
        # photon_flux is in ph/um/s/m^2
        # pupil_area in m^2
        # bandwidth in microns
        # int_time in seconds

        read_noise_tot = np.sqrt(read_noise*num_pix) #TODO is this read-noise scaling right?

        star_photons = photon_flux * throughput * pupil_area * bandwidth * int_time
        print("Stellar photons: %.3g" % star_photons)
        star_snr = (star_photons*QE) / read_noise_tot
        print('S/N ratio for star measurement: %f' % star_snr)

        companion_flux = star_photons * contrast
        raw_comp_snr = companion_flux / np.sqrt(star_photons + read_noise_tot**2)
        print('No-nulling S/N ratio for companion: %f' % raw_comp_snr)

        nulled_comp_snr = companion_flux / np.sqrt(star_photons*null_depth + read_noise_tot**2)
        print('Nulled S/N ratio for companion: %f' % nulled_comp_snr)

        return nulled_comp_snr