import matplotlib.pyplot as plt
import pywt
from padasip.filters.lms import FilterLMS
from ssnf import ssnf
import numpy as np
from scipy import signal

files = ['abdomen1', 'abdomen2', 'abdomen3', 'thorax1', 'thorax2']
DECOMPOSITION_SCALE = 5
FIGURE_RANGE = 20000


# Data I/O
def read_data(file_name: str):
    with open(file_name + '.txt') as f:
        return [float(x) for x in f.readlines()]


# Plotting
def add_plot(data: [float], max_len: int, ax: plt.Axes):
    ax.plot(range(min(max_len, len(data))), data[:min(len(data), max_len)])


def plot_data(data: [[float]], title: str = ''):
    f, ax = plt.subplots(len(files))
    f.suptitle(title)
    plt.subplots_adjust(hspace=1)
    for i, name in zip(range(len(files)), files):
        add_plot(data[i], FIGURE_RANGE, ax[i])
        ax[i].set_title(name)
    plt.draw()
    print('Drawn plot:', title)


def plot_single_data(data: [float], title: str = ''):
    plt.figure()
    plt.plot(list(range(FIGURE_RANGE)), data[:FIGURE_RANGE])
    plt.draw()
    print('Drawn plot:', title)


# Normalize input data
def normalize_data(data):
    mean = sum(data) / len(data)
    data = [d - mean for d in data]
    m = max(data)
    return [d / m for d in data]


def high_pass_filter(data, perc=0.2):
    return [d if abs(d) > (max(data) * perc) else 0 for d in data]


def pass_filter(data, s=10, e=1000):
    return s * [0] + data[s:e] + (len(data) - e) * [0]


# Fourier transform
def fourier(data: [float]):
    return [list(np.fft.fft(d)) for d in data]


# Wavelet transform
def wavelet(data: [float], style: str = 'haar'):
    a, d = pywt.dwt(data, style)
    return a, d


def inverse_wavelet(data: [float], detail: [float] = None, style: str = 'haar'):
    return pywt.idwt(cA=data, cD=detail, wavelet=style)


def stationary_wavelet(data: [float], style: str = 'haar'):
    return pywt.swt(data, style, level=DECOMPOSITION_SCALE)


def inverse_stationary_wavelet(data: [float], style: str = 'haar'):
    return pywt.iswt(coeffs=data, wavelet=style)


def use_d_wavelet(data: [[float]]):
    data = [stationary_wavelet(d, w_style) for d in data]
    # data = [([], [])]

    # Plot Transformed data
    plot_data([x for x, _ in data], 'Wavelet ({}) adjusted data'.format(w_style))
    plot_data([x for _, x in data], 'Wavelet detail data')

    # Transform back
    with_detail = inverse_wavelet([d for d, _ in data], [d for _, d in data], style=w_style)
    without_detail = inverse_wavelet([d for d, _ in data], style=w_style)
    return without_detail


def use_s_wavelet(data):
    data = [stationary_wavelet(d, w_style) for d in data]
    print(np.shape(data))
    # data = [[y[0] for y in x] for x in data]
    # print(np.shape(data))
    #
    # # LMS
    # results = []
    # for reference_data in data[3]:
    #     results.append([])
    #     for d in range(DECOMPOSITION_SCALE):
    #         y, _, _ = adaptive_filtering(data[0], reference_data[d])
    #         results[d].append(y)
    # # plot_single_data(y)

    thresholds = [1000 for x in range(DECOMPOSITION_SCALE)]
    data = [ssnf([x[0] for x in d], scales=DECOMPOSITION_SCALE, noise_thresholds=thresholds) for d in data]
    # Transform back
    return [inverse_stationary_wavelet(d, style=w_style) for d in data]


# LMS
def adaptive_filtering(original_input, ref_input):
    print('original_input', np.shape(original_input))
    print('ref_input', np.shape(ref_input))
    original_input = np.transpose(original_input)
    step_size = 0.1  # 0.0004
    no_filter_taps = 100
    weights = 'random'
    f = FilterLMS(len(original_input[0]), step_size, w=weights)
    return f.run(ref_input, original_input)


if __name__ == '__main__':
    data = [read_data(file_name) for file_name in files]

    # Plot given data
    plot_data(data, 'Given data')

    # Butter high pass filter
    sos = signal.butter(10, 0.6, 'hp', fs=1000, output='sos')
    data = [signal.sosfilt(sos, d) for d in data]
    plot_data(data, "Butter Filtered")

    # Normalize data
    data = [normalize_data(d) for d in data]
    plot_data(data, 'Normalized data')

    # FFT
    data_fft = fourier(data)
    plot_data(data_fft, "FFT")

    # data_fft_thorax = [(a+b)/2 for a, b in zip(data_fft[0], data_fft[1])]
    # data_fft_abdomen = [(a+b+c)/3 for a, b, c in zip(data_fft[2], data_fft[3], data_fft[4])]
    # data_ifft = np.fft.ifft([a-t for a, t in zip(data_fft_abdomen, data_fft_thorax)])
    # plot_single_data(data_ifft, "IFFT")
    # data_fft = [[a - b for a, b in zip(d, pass_filter(d, 300, 1000))] for d in data_fft]
    data_fft = [pass_filter(d, 300, 1000) for d in data_fft]
    plot_data(data_fft, "FFT Highpass")
    data_ifft = [np.fft.ifft(d) for d in data_fft]
    plot_data(data_ifft, "IFFT transformed")

    # Wavelet transform
    # w_style = 'haar'
    w_style = 'bior1.5'
    # w_style = 'db1'

    data_s_wavelet = use_s_wavelet(data)
    plot_data(data_s_wavelet, "With swt")

    data_ssnf = [x * a for x, a in zip(data_s_wavelet[4], data[4])]
    plot_single_data(data_ssnf, "SSNF on wavelets of data[4]")
    data_ssnf = high_pass_filter(normalize_data(data_ssnf), 0.15)
    plot_single_data(data_ssnf, "SSNF on wavelets of data[4], with highpass filter")
    # plot_single_data(data[4])
    # plot_single_data([data[4][i] if data_ssnf[i] == 0 else 0 for i in range(len(data_ssnf))])
    # Plot output data
    plot_data(data, title='Re-transformed data ({}, with detail)'.format(w_style))
    # plot_data([a - b for a, b in zip(with_detail, without_detail)],
    #           title='Difference re-transforms with/without detail')

    plt.show()
