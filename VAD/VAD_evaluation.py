import sys
import os
import scipy.io
import numpy as np
import librosa
from lib.python.VAD_test import VAD_test
from myMRCG.mrcg_extract import extract_mrcg_feats
from main_utils import frame2rawlabel, frame2inpt
import matplotlib.pyplot as plt
from itertools import groupby
from operator import itemgetter


def VAD_evaluation(audio_file, mode, threshold, output_type=1, is_default=1):
    os.system("rm -rf ./VAD/result")
    os.system("mkdir ./VAD/result")

    data_len, winlen, winstep, audio_sr = extract_mrcg_feats(audio_file)
    VAD_test(mode, data_len)
    pred = scipy.io.loadmat("./VAD/result/pred.mat")["pred"].squeeze()
    result = np.zeros(len(pred))
    result[pred > threshold] = 1

    if output_type == 1:
        result = frame2rawlabel(result, winlen, winstep)
        pred = frame2inpt(pred, winlen, winstep)

    return result, pred, audio_sr


def result_plot(audio_file, mode=0, threshold=0.4):
    result, pred, _ = VAD_evaluation(audio_file, mode, threshold)
    speech, sr = librosa.load(audio_file, sr=16000)

    t = np.arange(1, len(speech)+1) / sr
    p1 = plt.plot(t, speech)
    p2 = plt.plot(t[0:len(result)], result * 0.15, 'r')
    plt.xlim((0, t[-1]))
    plt.ylim((-0.3, 0.6))
    plt.legend(p2, 'prediction')
    plt.show()


def get_time_intervals(audio_file, mode=0, threshold=0.4, sil_threshold=0.1, duration_threshold=0.5):
    # mode 0: ACAM3, 1: bDNN, 2: DNN, 3: LSTM
    result, pred, audio_sr = VAD_evaluation(audio_file, mode, threshold)
    sil_threshold_point = sil_threshold * audio_sr
    duration_threshold_point = duration_threshold * audio_sr
    audio_sr = float(audio_sr)
    result_invert = np.logical_not(result)
    sil_idx = np.where(result_invert)[0]
    sil_idx_group = []
    time_intervals = []
    for k, g in groupby(enumerate(sil_idx), lambda ix: ix[0] - ix[1]):
        consecutive = list(map(itemgetter(1), g))
        sil_idx_group.append(consecutive)

    for i, c in enumerate(sil_idx_group):
        if i == 0:
            begin = c[-1] + 1
            continue
        elif i == len(sil_idx_group) - 1:
            end = c[0] - 1
            if end - begin + 1 >= duration_threshold_point:
                time_intervals.append((begin / audio_sr, end / audio_sr))
        else:
            if len(c) >= sil_threshold_point:
                end = c[0] - 1
                if end - begin + 1 >= duration_threshold_point:
                    time_intervals.append((begin / audio_sr, end / audio_sr))
                begin = c[-1] + 1
            else:
                continue
    return time_intervals