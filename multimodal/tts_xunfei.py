# -*- coding:utf-8 -*-
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import os


class XunfeiTTSGenerator:
    """
    讯飞 TTS 语音合成模块 (WebSocket版)
    """

    def __init__(self, app_id: str, api_key: str, api_secret: str):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.host_url = 'wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6'
        self.voice_name = "x6_lingfeiyi_pro"

    def _create_auth_url(self):
        # 解析URL获取host和path用于签名
        stidx = self.host_url.index("://")
        host_path = self.host_url[stidx + 3:]
        edidx = host_path.index("/")
        host = host_path[:edidx]
        path = host_path[edidx:]

        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 签名构造
        signature_origin = "host: {}\ndate: {}\nGET {} HTTP/1.1".format(host, date, path)
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.api_key, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        values = {"host": host, "date": date, "authorization": authorization}
        return self.host_url + "?" + urlencode(values)

    def generate(self, text: str, student_level: str, save_dir: str):
        """
        核心生成方法：传入提取出的纯净课文，生成 mp3
        """
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")
        file_path = os.path.join(save_dir, f"{student_level}_{timestamp}.mp3")

        if os.path.exists(file_path):
            os.remove(file_path)

        auth_url = self._create_auth_url()

        # 内部回调函数，用于处理 WebSocket 流程
        def on_message(ws, message):
            try:
                res = json.loads(message)
                code = res["header"]["code"]
                if code != 0:
                    print(f"❌ 讯飞错误: {res['header']['message']}")
                    ws.close()
                else:
                    audio = base64.b64decode(res["payload"]["audio"]["audio"])
                    status = res["payload"]["audio"]["status"]
                    with open(file_path, 'ab') as f:
                        f.write(audio)
                    if status == 2:
                        print(f"✅ 音频合成成功: {os.path.basename(file_path)}")
                        ws.close()
            except Exception as e:
                print("解析异常:", e)

        def on_open(ws):
            def run(*args):
                d = {
                    "header": {"app_id": self.app_id, "status": 2},
                    "parameter": {
                        "tts": {
                            "vcn": self.voice_name, "volume": 50, "speed": 50, "pitch": 50,
                            "audio": {"encoding": "lame", "sample_rate": 24000}
                        }
                    },
                    "payload": {
                        "text": {
                            "encoding": "utf8", "status": 2,
                            "text": str(base64.b64encode(text.encode('utf-8')), "UTF8")
                        }
                    }
                }
                ws.send(json.dumps(d))

            thread.start_new_thread(run, ())

        ws = websocket.WebSocketApp(
            auth_url,
            on_message=on_message,
            on_error=lambda ws, e: print(f"### error: {e}"),
            on_close=lambda ws, st, msg: None
        )
        ws.on_open = on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        return file_path