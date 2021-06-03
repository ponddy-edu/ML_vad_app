from myMRCG.utils import MRCG_features, Frame_Length, Truelabel2Trueframe
import librosa
import os
import shutil
import numpy as np
import scipy.io


def extract_mrcg_feats(filename):
    cwd = os.getcwd()
    folder = os.path.join(cwd, "VAD/sample_data")
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(e)
    os.makedirs(os.path.join(folder, "Labels"))

    noisy_speech, audio_sr = librosa.load(filename, sr=16000)
    feat = MRCG_features(noisy_speech, audio_sr).T   # shape: (frames, 768)
    if feat.shape[0] > noisy_speech.shape[0]:
        feat = feat[noisy_speech.shape[0], :]

    winlen = int(np.ceil(audio_sr*25*0.001))     # window length (default : 25 ms)
    winstep = int(np.ceil(audio_sr*10*0.001))    # window step (default: 10 ms)
    train_mean = np.mean(feat, 1)
    train_std = np.std(feat, 1)
    y_labels = np.zeros([len(noisy_speech), 1])
    framed_labels = Truelabel2Trueframe(y_labels, winlen, winstep)

    if len(feat) > len(framed_labels):
        feat = feat[:len(framed_labels), :]
        data_len = len(framed_labels)
    else:
        framed_labels = framed_labels[:len(feat), 1]
        data_len = len(feat)

    opf_mrcg_spec = open(os.path.join(folder, "mrcg_spec.txt"), "w")
    opf_mrcg_spec.write(f"{data_len},{feat.shape[1]},float32")
    opf_label_spec = open(os.path.join(folder, "Labels", "label_spec.txt"), "w")
    opf_label_spec.write(f"{data_len},1,float32")

    feat = feat.T   # transpose again to behave the same as matlab
    feat.astype("float32").tofile(os.path.join(folder, "mrcg.bin"))
    framed_labels.astype("float32").tofile(os.path.join(folder, "Labels", "label.bin"))
    scipy.io.savemat(os.path.join(folder, "normalize_factor.mat"), mdict={'train_mean': train_mean, 'train_std': train_std})

    return data_len, winlen, winstep, audio_sr

if __name__ == "__main__":
    extract_mrcg_feats("/home/george/Downloads/eat.wav")