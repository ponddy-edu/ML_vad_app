import datetime
import time

f = open("ted_caption.srt", "r")


def time2sec(input_time):
    ms = int(input_time.split(",")[1]) / 1000.0
    x = time.strptime(input_time.split(',')[0], '%H:%M:%S')
    result = datetime.timedelta(hours=x.tm_hour, minutes=x.tm_min, seconds=x.tm_sec).total_seconds() + ms
    return result

tmp = []
all_transcript = []
while True:
    line = f.readline()
    if not line:
        break
    if line == "\n":
        origin_begin = tmp[1].split(" --> ")[0]
        origin_end = tmp[1].split(" --> ")[1]
        begin_time = time2sec(origin_begin)
        end_time = time2sec(origin_end)
        sen = "，".join(tmp[2:])
        all_transcript.append((sen, begin_time, end_time))
        tmp = []
    else:
        tmp.append(line.strip())