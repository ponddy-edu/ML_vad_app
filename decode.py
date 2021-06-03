# -*- coding: utf-8 -*-
import os, sys, tempfile
import time, shutil
import subprocess
import json
import numpy as np
from argparse import ArgumentParser
from collections import deque


def runDecode(prjDir, dirID, dirname, langDir="lang", modelDir="exp/tri2", ivecExtractor="exp/nnet3/extractor"):
    os.system(f"rm -rf {prjDir}/exp/nnet3/tdnn_sp/tmp")
    
    langDir = os.path.join(prjDir, langDir)
    modelDir = os.path.join(prjDir, modelDir)

    try:
        sort_cmd = 'cat %s/utt2spk | %s/utils/utt2spk_to_spk2utt.pl | sort > %s/spk2utt' % (dirname, prjDir, dirname)
        subprocess.call(sort_cmd, shell=True)
    except subprocess.CalledProcessError as err:
        print('Error in generating spk2utt')

    for file in os.listdir(dirname):
        if os.path.isfile(file):
            with open(os.path.join(dirname, file), 'r') as f:
                print('Content of file %s' % file)
                tmp = f.read()
                print(tmp)

    try:
        mfcc_cmd = '%s/steps/make_mfcc.sh --nj 1 --mfcc-config %s/conf/mfcc_hires.conf \
                    %s %s/mfcc/log %s/mfcc/features' % (prjDir, prjDir, dirname, dirname, dirname)
        subprocess.call(mfcc_cmd, shell=True)
    except subprocess.CalledProcessError as err:
        print('Error in extracting mfcc features')

    shutil.copy2(dirname+'/mfcc/features/raw_mfcc_audio.1.scp', dirname+'/mfcc/features/feats.scp')
    shutil.copy2(dirname+'/mfcc/features/raw_mfcc_audio.1.scp', dirname+'/feats.scp')

    try:
        cmvn_cmd = '%s/steps/compute_cmvn_stats.sh %s %s/mfcc/log %s/mfcc/features' % (prjDir, dirname, dirname, dirname)
        subprocess.call(cmvn_cmd, shell=True)
    except subprocess.CalledProcessError as err:
        print('Error in extracting cmvn features')

    extractor = prjDir+'/'+ivecExtractor
    try:
        ivector_cmd = '%s/steps/online/nnet2/extract_ivectors_online.sh --nj 1 \
                        %s %s %s/ivector/' % (prjDir, dirname, extractor, dirname)
        subprocess.call(ivector_cmd, shell=True)
    except subprocess.CalledProcessError as err:
        print('Error in extracting ivector')

    ivectorDir = dirname+'/ivector/'
    try:
        decode_cmd = f"steps/nnet3/decode.sh --nj 1 --cmd run.pl --online-ivector-dir \
                {dirname}/ivector {modelDir}/graph {dirname} {prjDir}/exp/nnet3/tdnn_sp/tmp"
        subprocess.call(decode_cmd, shell=True)

    except subprocess.CalledProcessError as err:
        print('Error in dnn decoding')

    # try:
    #     subprocess.call("bash path.sh", shell=True)
    # except subprocess.CalledProcessError as err:
    #     print("Error in path.sh: ", err)

    decodeDir = f"{prjDir}/exp/nnet3/tdnn_sp/tmp"
    try:
        align_decode_cmd = f"gunzip -c {decodeDir}/lat.1.gz > {decodeDir}/1.lats | lattice-align-words-lexicon --partial-word-label=4324 \
            --max-expand=10.0 --test=true {langDir}/phones/align_lexicon.int {prjDir}/exp/nnet3/tdnn_sp/final.mdl ark:{decodeDir}/1.lats \
            ark:- | lattice-to-ctm-conf --acoustic-scale=0.1 ark:- {decodeDir}/result.ctm"
        subprocess.call(align_decode_cmd, shell=True)
    except subprocess.CalledProcessError as err:
        print('Error in dnn decoding align')


def parseTranscript():
    trans_list = []
    cur_path = os.getcwd()
    print(cur_path)
    print(os.path.join(cur_path, "exp/nnet3/tdnn_sp/tmp/scoring_kaldi/penalty_0.0/17.txt"))
    f = open(os.path.join(cur_path, "exp/nnet3/tdnn_sp/tmp/scoring_kaldi/penalty_0.0/17.txt"), "r")
    lines = f.readlines()
    print("=========================================")
    for line in lines:
        line = line.strip()
        sen_id = line.split()[0]
        text = " ".join(line.split()[1:])
        trans_list.append((sen_id, text))
    return trans_list


def parseCTM():
    cur_path = os.getcwd()
    wd_lines = open(os.path.join(cur_path, "lang/words.txt"), "r").readlines()
    ctm_idx2wd = []
    for line in wd_lines:
        wd = line.split()[0]
        ctm_idx2wd.append(wd)

    f_ctm = open(os.path.join(cur_path, "exp/nnet3/tdnn_sp/tmp/result.ctm"), "r")
    lines_ctm = f_ctm.readlines()

    utt_idx_now = ""
    final_ctm = {}
    ctm_list = []
    final_text = {}
    tmp_text = []

    for i, line in enumerate(lines_ctm):
        line = line.strip()
        utt, _, begin, duration, idx, score = line.split()
        end = str("{:.2f}".format(float(begin) + float(duration)))
        utt_idx = utt.split("_")[-1]
        if i == 0:
            utt_idx_now = utt_idx
        else:
            if utt_idx != utt_idx_now:
                final_ctm[int(utt_idx_now)] = ctm_list
                final_text[int(utt_idx_now)] = " ".join(tmp_text)
                utt_idx_now = utt_idx
                ctm_list = []
                tmp_text = []

        tmp_text.append(ctm_idx2wd[int(idx)])
        ctm_list.append({"begin": begin, "end": end, "word": ctm_idx2wd[int(idx)], "score": score})

        if i == len(lines_ctm)-1:
            final_ctm[int(utt_idx)] = ctm_list
            final_text[int(utt_idx_now)] = " ".join(tmp_text)

    return final_ctm, final_text