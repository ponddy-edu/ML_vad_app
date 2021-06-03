import subprocess
import os
import time
import numpy as np
from VAD.slice_audio import slice_audio
from decode import runDecode, parseCTM # parseTranscript


def audio2transcript(wav_filepath, mode=0, voice_energy_threshold=0.4, silence_duration_threshold=0.1, voice_duration_threshold=0.5):
    dirID = str(round(time.time() * 1000))
    cur_path = os.getcwd()
    dirname = os.path.join(cur_path, 'audio')#'audio_' + dirID)

    if not os.path.exists(dirname):
        os.makedirs(dirname)

    time_intervals, file_list = slice_audio(
        wav_filepath,
        os.path.join(dirname, "audio_clips"),
        mode=mode,
        threshold=voice_duration_threshold,
        sil_threshold=silence_duration_threshold,
        duration_threshold=voice_duration_threshold)
    # print(file_list)
    # print(time_intervals)

    opf_text = open(os.path.join(dirname, "text"), "w")
    opf_utt2spk = open(os.path.join(dirname, "utt2spk"), "w")
    opf_wavscp = open(os.path.join(dirname, "wav.scp"), "w")

    wavclip_filepath_list = []
    for f_name in file_list:
        basename = os.path.splitext(f_name)[0]
        file_path = os.path.join(dirname, "audio_clips", f_name)
        opf_text.write(basename + "\n")
        opf_utt2spk.write(basename + " 0\n")
        opf_wavscp.write(basename + " " + file_path + "\n")
        wavclip_filepath_list.append(os.path.join("audio", "audio_clips", f_name))

    opf_text.close()
    opf_utt2spk.close()
    opf_wavscp.close()

    os.chdir("wordbased_asr")
    runDecode(os.path.join(cur_path, "wordbased_asr"), dirID, dirname)
    #transcripts = parseTranscript()
    ctm_dict, transcripts = parseCTM()
    # print(transcripts)

    final_list = []
    for i, time_interval in enumerate(time_intervals):
        if i not in ctm_dict:
            continue
        cur = {}
        cur["text"] = transcripts[i]
        cur["intervals"] = list(time_interval)
        cur["ctm"] = ctm_dict[i]
        cur["wavclip_filepath"] = wavclip_filepath_list[i]
        final_list.append(cur)
    # print(final_list)
    return final_list

if __name__ == "__main__":
    audio2transcript("./uploads/001.wav")
