import socketserver
import json
import time
import copy
import os
import PIL.Image
import re
import datetime

info = {
    "cmd": "car",
    "value": {
        "Serial": "XXXXXXXXXXXXXXXXXXXX",
        "Locomotive": True,
        "Speed": 60,
        "OrderNum": "",
        "TrainKind": "",
        "TrainNo": ""
    }
}

info_img = {
    "cmd": "car",
    "value": {
        "Serial": "XXXXXXXXXXXXXXXXXXXX",
        "Locomotive": True,
        "Speed": 60,
        "OrderNum": "",
        "TrainKind": "",
        "TrainNo": "",
        "TrainDate": "",
        "Image": {
            "ChannelNum": 1,
            "Width": "",
            "Height": "",
            "Length": ""
        }
    }
}

_interval_s = 0
_img = 1


def read_pic_data(f):
    with open(f, 'rb') as fr:
        data = fr.read()
    return data


def get_pic_jcode_data(b_data):
    # 获取图片车轮二进制数据
    s_jcode = "\<JCODE\s\=\s.{20}\>"
    s_jcode_value = "(?<=\s\=\s).{20}"
    try:
        data = re.search(s_jcode, str(b_data))
        d = data.group()
        r = re.search(s_jcode_value, d)
        rd = r.group()
        return rd
    except:
        return None


def generate_data():
    data = None
    r = list()
    index = 1
    with open("data.txt", "r") as fr:
        data = fr.readlines()
    _train_no_ = None
    _train_date_ = None
    if len(data) > 0:
        for l in data:
            current = copy.deepcopy(info_img if _img == 1 else info)
            current["value"]["OrderNum"] = str(index).zfill(3)
            index += 1
            dd = get_pic_jcode_data(read_pic_data(l.strip()))

            if dd is not None:
                current["value"]["Serial"] = dd
                if dd[0] == "J":
                    current["value"]["TrainNo"] = _train_no_ = dd[12:19]
                    if _img == 1:
                        n = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                        current["value"]["TrainDate"] = _train_date_ = n
                else:
                    current["value"]["TrainNo"] = _train_no_
                    if _img == 1:
                        current["value"]["TrainDate"] = _train_date_
                    if dd[0] == "K":
                        current["value"]["TrainKind"] = dd[1:4]
                    else:
                        current["value"]["TrainKind"] = dd[1]
            else:
                _kind = l.strip().split('_')[0]
                _kind_bits = len(_kind)
                current["value"]["Serial"] = _kind + 'X'*(20-_kind_bits)
                current["value"]["TrainNo"] = _train_no_
                if _img == 1:
                    current["value"]["TrainDate"] = _train_date_
                if _kind[0] == "K":
                    current["value"]["TrainKind"] = _kind
                else:
                    current["value"]["TrainKind"] = _kind[1]

            if _img == 1:
                file_info = os.stat(l.strip())
                p = PIL.Image.open(l.strip())
                current["value"]["Image"]["Width"] = p.width
                current["value"]["Image"]["Height"] = p.height
                current["value"]["Image"]["Length"] = file_info.st_size
                current["value"]["Image"]["ChannelNum"] = 1
                r.append(json.dumps(current).encode() + b"\r\n")
                with open(l.strip(), "rb") as frb:
                    r.append("////" + l.strip())
            else:
                r.append(json.dumps(current).encode() + b"\r\n")
            r.append("")
    return r

class Test(socketserver.BaseRequestHandler):
    def handle(self):
        print('连接来自:', self.client_address)
        while True:
            d = generate_data()

            for v in d:
                if v == "":
                    time.sleep(_interval_s)
                elif isinstance(v, str) and "////" in v:
                    fo = open(v[4:], 'rb')
                    while True:
                        filedata = fo.read()
                        if not filedata:
                            break
                        self.request.sendall(filedata)
                    fo.close()
                else:
                    # self.request.sendto(v, self.client_address)
                    self.request.send(v)
                    # time.sleep(1)


if __name__ == "__main__":
    setting = None
    with open("main.json", "r") as fr:
        setting = json.load(fr)
    _interval_s = int(setting["car_interval_s"])
    host = setting["ip"]
    port = int(setting["port"])
    _img = int(setting["img"])
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    socketserver.ThreadingTCPServer.daemon_threads = True
    server = socketserver.ThreadingTCPServer((host, port), Test) #实现了多线程的socket通话
    server.serve_forever()