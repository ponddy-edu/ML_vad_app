import numpy as np


def frame2rawlabel(label, win_len, win_step):
    num_frame = len(label)

    total_len = (num_frame - 1) * win_step + win_len

    raw_label = np.zeros(total_len)
    start_idx = 0
    i = 0
    while True:
        if start_idx + win_len > total_len:
            break
        if i == 0:
            raw_label[start_idx:start_idx + win_len] = label[i]
        else:
            temp_label = label[i]
            raw_label[start_idx:start_idx + win_len] = raw_label[start_idx:start_idx + win_len] + temp_label
        i += 1
        start_idx += win_step

    raw_label = (raw_label >= 1)
    return raw_label


def moving_mean(x, N):
    sum = 0
    ceil_val = int(np.ceil(N/2))
    floor_val = int(np.floor(N/2))
    if ceil_val >= len(x):
        return np.repeat(np.mean(x), len(x))
    result = np.zeros(len(x))
    for i in range(len(x)):
        begin_idx = 0 if i <= floor_val else i - floor_val
        end_idx = ceil_val+i if i < len(x) - ceil_val else len(x)
        result[i] = np.mean(x[begin_idx:end_idx])

    return result


def frame2inpt(label, win_len, win_step):
    num_frame = int(len(label))

    total_len = (num_frame - 1) * win_step + win_len

    raw_label = np.zeros(total_len)
    start_idx = 0
    i = 0
    while True:
        if start_idx + win_len > total_len:
            break
        if i == 0:
            raw_label[start_idx:start_idx + win_len] = label[i]
        else:
            temp_label = label[i]
            raw_label[start_idx:start_idx + win_len] = (raw_label[start_idx:start_idx + win_len] + temp_label) / 2
        i += 1
        start_idx += win_step

    raw_label = moving_mean(raw_label, 20)
    return raw_label


if __name__ == "__main__":
    print("hello")