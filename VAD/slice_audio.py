import sys
sys.path.insert(0, './VAD')
from VAD_evaluation import get_time_intervals
from pydub import AudioSegment
import os


def slice_audio(audio_file, output_path, mode=0, threshold=0.4, sil_threshold=0.1, duration_threshold=0.5):
    os.system(f"rm -rf {output_path}")
    os.system(f"mkdir {output_path}")
    dir_path = output_path
    filename = os.path.splitext(audio_file.split("/")[-1])[0]

    wav = AudioSegment.from_wav(audio_file)
    time_intervals = get_time_intervals(audio_file=audio_file, mode=mode, threshold=threshold, sil_threshold=sil_threshold, duration_threshold=duration_threshold)
    file_list = []
    
    for i, time_mark in enumerate(time_intervals):
        begin, end = time_mark
        audioSeg = wav[begin*1000:end*1000]
        #begin = "{0:.2f}".format(round(begin, 2))
        #end = "{0:.2f}".format(round(end, 2))
        i = "{0:0=4d}".format(i)
        segFileName = f"{filename}_{i}.wav"
        file_list.append(segFileName)
        audioSeg.export(os.path.join(dir_path, segFileName), format="wav")
    return time_intervals, file_list