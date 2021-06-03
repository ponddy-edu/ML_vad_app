import os
import sys
import subprocess
import json
import re
import numpy as np
import pandas as pd
import time
import pafy
from flask import Flask, request, redirect, url_for, send_file, flash, jsonify, Response, send_from_directory
from werkzeug import secure_filename
from video_transcript import audio2transcript

UPLOAD_FOLDER = 'uploads'
VIDEO_FOLDER = 'videos'
AUDIO_FOLDER = 'audio'
ALLOWED_EXTENSIONS = set(['avi', 'mp4', 'webm', 'mov', 'flv', 'mpg', 'wmv', 'mkv'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['VIDEO_FOLDER'] = VIDEO_FOLDER
app.config['AUDIO_FOLDER'] = AUDIO_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def remove_files_in_folder(folder):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)


def get_ffmpeg_subclip_cmd(filename, t1, t2, targetname):
    t_duration = t2-t1
    cmd = f"ffmpeg -y -i {filename} -ss {t1} -t {t_duration} -strict -2 {targetname}"
    #subprocess.call(cmd, shell=True)
    return cmd


@app.route('/')
def root():
    return send_file('index.html')


@app.route('/scripts/<path:path>')
def send_js(path):
    return send_from_directory('scripts', path)


@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('css', path)


@app.route('/videos/<path:path>')
def send_video(path):
    return send_from_directory('videos', path)

@app.route('/audio/audio_clips/<path:path>')
def send_audio_clips(path):
    return send_from_directory('audio/audio_clips', path)


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        video_input_mode = int(request.form['video_mode'])
        mode = int(request.form['model'])
        voice_threshold = float(request.form['voice_threshold'])
        sil_duration_threshold = float(request.form['sil_duration_threshold'])
        voice_duration_threshold = float(request.form['voice_duration_threshold'])
        current_dir = os.getcwd()

        if video_input_mode == 0:
            youtube_url = request.form['youtube-url']
            if not youtube_url:
                return jsonify({"error": True, "err_msg": "Youtube video url not found"})

            remove_files_in_folder(app.config['UPLOAD_FOLDER'])
            remove_files_in_folder(app.config['VIDEO_FOLDER'])
            remove_files_in_folder(app.config['AUDIO_FOLDER'])

            v = pafy.new(youtube_url)
            s = v.getbest()
            time_stamp = str(round(time.time() * 1000))
            video_name = f"temp_{time_stamp}"
            video_ext = s.extension
            videopath = s.download(os.path.join(app.config['UPLOAD_FOLDER'], f"{video_name}.{video_ext}"))
            wavpath = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{time_stamp}.wav")

        elif video_input_mode == 1:

            if 'file' not in request.files:
                print('No file in requested data...')
                return jsonify({"error": True, "err_msg": "No file in requested data"})

            file = request.files['file']

            if not file.filename:
                print('No file selected...')
                return jsonify({"error": True, "err_msg": "No file selected"})

            if file and allowed_file(file.filename):
                # remove previous files
                remove_files_in_folder(app.config['UPLOAD_FOLDER'])
                remove_files_in_folder(app.config['VIDEO_FOLDER'])

                # files config
                time_stamp = str(round(time.time() * 1000))
                video_name, video_ext = os.path.splitext(file.filename)
                videoname = secure_filename(video_name + "_" + time_stamp + video_ext)
                wavname = secure_filename(video_name + "_" + time_stamp + ".wav")
                videopath = os.path.join(app.config['UPLOAD_FOLDER'], videoname)
                wavpath = os.path.join(app.config['UPLOAD_FOLDER'], wavname)

                # save uploaded file
                file.save(videopath)
            else:
                return jsonify({"error": True, "err_msg": "Not allowed file!"})

        # extract audio from video
        try:
            extract_audio_cmd = f"ffmpeg -i {videopath} -vn -acodec pcm_s16le -ar 16000 -ac 1 -y {wavpath}"
            subprocess.call(extract_audio_cmd, shell=True)
        except:
            return jsonify({"error": True, "err_msg": "Error occured when extracting audio from video."})

        # predict ctm and transcriptions
        try:
            result = audio2transcript(
                wav_filepath=wavpath,
                mode=mode,
                voice_energy_threshold=voice_threshold,
                silence_duration_threshold=sil_duration_threshold,
                voice_duration_threshold=voice_duration_threshold)
        except:
            return jsonify({"error": True, "err_msg": "Error occured when generating transcripts from audio."})

        os.chdir(current_dir)
        return_result = []
        cmd2write = []

        for i, d in enumerate(result):
            if not d["text"]:
                continue
            tmp = {}
            begin_time, end_time = d['intervals']
            t_duration = end_time - begin_time
            trg_fname = os.path.join(app.config['VIDEO_FOLDER'], f"{video_name}_{i}.{video_ext}")
            tmp["filename"] = trg_fname
            tmp["text"] = d["text"]
            tmp["ctm"] = d["ctm"]
            tmp["wavclip_filepath"] = d["wavclip_filepath"]
            return_result.append(tmp)
            cmd = get_ffmpeg_subclip_cmd(videopath, begin_time, end_time, targetname=trg_fname)
            cmd2write.append(cmd + "\n")

        np.save("test.npy", return_result)

        cmd_filename = os.path.join(app.config['UPLOAD_FOLDER'], "video_subclip_cmd")
        cmd_file = open(cmd_filename, "w")
        cmd_file.writelines(cmd2write)
        cmd_file.close()

        video_supclip_cmd = f"parallel --jobs 12 < {cmd_filename}"
        subprocess.call(video_supclip_cmd, shell=True)

        return jsonify({"error": False, "err_msg": "None", "data": return_result, "origin_video": videopath, "origin_audio": wavpath})


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == "__main__":
    app.run(host='68.255.152.146', port=5002, debug=False)
