# Ref
# github: https://github.com/jtkim-kaist/VAD

import numpy as np
import scipy.io
from myMRCG.olafilt import olafilt
from scipy.signal import lfilter
np.warnings.filterwarnings('ignore')


def hz2erb(hz):
    # Convert normal frequency scale in hz to ERB-rate scale.
    # Units are number of Hz and number of ERBs.
    # ERB stands for Equivalent Rectangular Bandwidth.
    # Written by ZZ Jin, and adapted by DLW in Jan'07
    erb = 21.4 * np.log10(4.37e-3*hz+1)
    return erb


def erb2hz(erb):
    # Convert ERB-rate scale to normal frequency scale.
    # Units are number of ERBs and number of Hz.
    # ERB stands for Equivalent Rectangular Bandwidth.
    # Written by ZZ Jin, and adapted by DLW in Jan'07
    hz = (np.power(10, (erb / 21.4)) - 1) / 4.37e-3
    return hz


def loudness(freq):
    # Compute loudness level in Phons on the basis of equal-loudness functions.
    # It accounts a middle ear effect and is used for frequency-dependent
    # gain adjustments.
    # This function uses linear interpolation of a lookup table to compute the
    # loudness level, in phons, of a pure tone of frequency freq using the
    # reference curve for sound pressure level dB. The equation is taken from
    # section 4 of BS3383.
    # Written by ZZ Jin, and adapted by DLW in Jan'07
    dB = 60
    mat = scipy.io.loadmat("./VAD/myMRCG/f_af_bf_cf.mat")
    if freq < 20 or freq > 12500:
        return
    i = 1

    ff = np.squeeze(mat["ff"])
    af = np.squeeze(mat["af"])
    bf = np.squeeze(mat["bf"])
    cf = np.squeeze(mat["cf"])

    while(ff[i] < freq):
        i += 1

    afy = af[i-1] + (freq - ff[i-1]) * \
        (af[i] - af[i-1]) / (ff[i] - ff[i-1])
    bfy = bf[i-1] + (freq - ff[i-1]) * \
        (bf[i] - bf[i-1]) / (ff[i] - ff[i-1])
    cfy = cf[i-1] + (freq - ff[i-1]) * \
        (cf[i] - cf[i-1]) / (ff[i] - ff[i-1])
    loud = 4.2 + afy * (dB-cfy) / (1 + bfy * (dB-cfy))
    return loud


def gammatone(sig_in, numChan=128, fRange=[80, 5000], fs=16000):
    # Produce an array of filtered responses from a Gammatone filterbank.
    # The first variable is required.
    # numChan: number of filter channels.
    # fRange: frequency range.
    # fs: sampling frequency.
    # Written by ZZ Jin, adapted by DLW in Jan'07 and JF Woodruff in Nov'08
    filterOrder = 4     # filter order
    gL = 2048   # gammatone filter length or 128 ms for 16 kHz sampling rate
    fRange = np.array(fRange)

    sigLength = len(sig_in)
    phase = np.zeros(numChan)  # initial phases
    erb_b = hz2erb(fRange)   # upper and lower bound of ERB29
    erb = np.linspace(erb_b[0], erb_b[1], numChan)  # ERB segment
    cf = erb2hz(erb)     # center frequency array indexed by channel
    b = 1.019 * 24.7 * (4.37 * cf / 1000 + 1)   # rate of decay or bandwidth

    # Generating gammatone impulse responses with middle-ear gain normalization
    gt = np.zeros((numChan, gL))    # Initialization
    tmp_t = np.arange(1, gL+1) / fs
    for i in range(numChan):
        gain = 10**((loudness(cf[i]) - 60) / 20) / 3 * \
            (2 * np.pi * b[i] / fs)**4    # loudness-based gain adjustments
        gt[i, :] = gain * fs**3 * tmp_t**(filterOrder-1) * \
            np.exp(-2*np.pi*b[i]*tmp_t) * \
            np.cos(2*np.pi*cf[i]*tmp_t+phase[i])
    # sig = np.reshape(sig_in, (sigLength, 1)) # convert input to column vector

    # gammatone filtering using FFTFILT
    r = np.zeros((numChan, sigLength))
    for i in range(numChan):
        tmp = olafilt(gt[i], sig_in)
        r[i][:] = tmp
    return r


def cochleagram(r, winShift, winLength=320):
    # Generate a cochleagram from responses of a Gammatone filterbank.
    # It gives the log energy of T-F units
    # The first variable is required.
    # winLength: window (frame) length in samples
    # Written by ZZ Jin, and adapted by DLW in Jan'07
    winShift = int(winShift)
    winLength = int(winLength)
    numChan, sigLength = r.shape

    increment = winLength / winShift
    M = np.floor(sigLength / winShift).astype(int)

    # calculate energy for each frame in each channel
    a = np.zeros((numChan, M))
    for m in range(M):
        for i in range(numChan):
            if m+1 < increment:       # shorter frame lengths for beginning frames
                a[i, m] = np.dot(r[i, 0:(m+1)*winShift], r[i, 0:(m+1)*winShift])
            else:
                startpoint = int((m + 1 - increment) * winShift)
                a[i, m] = np.dot(r[i, startpoint:startpoint+winLength], r[i, startpoint:startpoint+winLength])
    return a


def get_avg(m, v_span, h_span):
    # This function produces a smoothed version of cochleagram
    nr, nc = m.shape
    out = np.zeros((nr, nc))
    fil_size = (2 * v_span + 1) * (2 * h_span + 1)

    for i in range(nr):
        row_begin = 0
        row_end = nr
        col_begin = 0
        col_end = nc

        if (i - v_span) >= 0:
            row_begin = i - v_span
        if (i + v_span) <= nr-1:
            row_end = i + v_span + 1

        for j in range(nc):
            if (j - h_span) >= 0:
                col_begin = j - h_span
            if (j + h_span) <= nc-1:
                col_end = j + h_span + 1

            tmp = m[row_begin:row_end, col_begin:col_end]
            out[i, j] = np.sum(tmp) / fil_size
    return out


def deltas(x, w=9):
    nr, nc = x.shape

    # Define window shape
    hlen = np.floor(w/2)
    w = 2*hlen + 1
    win = np.arange(hlen, -hlen-1, -1)

    # pad data by repeating first and last columns
    xx = np.hstack((np.tile(x[:, 0], (int(hlen), 1)).T, x, np.tile(x[:, -1], (int(hlen), 1)).T))

    d = lfilter(win, 1, xx, 1)  # filter along dim 1 (rows)

    d = d[:, int(2*hlen):int(2*hlen)+nc]

    return d


def MRCG_features(sig, sampFreq):
    # This function compute MRCG features
    beta = 1000 / np.sqrt(np.sum(sig**2) / len(sig))
    sig = sig * beta
    # sig = np.reshape(sig, (sig.shape[0], 1))
    g = gammatone(sig, 64, [50, 8000], sampFreq)    # Gammatone filterbank responses

    cochlea1 = cochleagram(g, winLength=sampFreq*0.025, winShift=sampFreq*0.010)
    cochlea1[cochlea1 == 0] = 10**-100    # Avoid zero encountered in log10
    cochlea1 = np.log10(cochlea1)

    cochlea2 = cochleagram(g, winLength=sampFreq*0.200, winShift=sampFreq*0.010)
    cochlea2[cochlea2 == 0] = 10**-100    # Avoid zero encountered in log10
    cochlea2 = np.log10(cochlea2)

    cochlea3 = get_avg(cochlea1, 5, 5)
    cochlea4 = get_avg(cochlea1, 11, 11)
    all_cochleas = np.vstack((cochlea1, cochlea2, cochlea3, cochlea4))
    delta = deltas(all_cochleas)
    ddelta = deltas(deltas(all_cochleas, 5), 5)

    mrcg_feat = np.vstack((all_cochleas, delta, ddelta))
    return mrcg_feat


def Frame_Length(x, overlap, nwind):
    nx = len(x)
    noverlap = nwind - overlap
    framelen = int((nx - noverlap) / (nwind - noverlap))
    return framelen


def Truelabel2Trueframe(TrueLabel_bin, wsize, wstep):
    iidx = 0
    Frame_iidx = 0
    Frame_len = Frame_Length(TrueLabel_bin, wstep, wsize)
    Detect = np.zeros([Frame_len, 1])
    while True:
        if iidx+wsize <= len(TrueLabel_bin):
            TrueLabel_frame = TrueLabel_bin[iidx:iidx + wsize - 1]*10
        else:
            TrueLabel_frame = TrueLabel_bin[iidx:]*10

        if (np.sum(TrueLabel_frame) >= wsize / 2):
            TrueLabel_frame = 1
        else:
            TrueLabel_frame = 0

        if (Frame_iidx >= len(Detect)):
            break

        Detect[Frame_iidx] = TrueLabel_frame
        iidx = iidx + wstep
        Frame_iidx = Frame_iidx + 1
        if (iidx > len(TrueLabel_bin)):
            break

    return Detect
