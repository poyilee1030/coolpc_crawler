
import requests


class LineNotify:
    def __init__(self):
        # LINE Notify 權杖
        self.token = "6CiLadqZ4mEMsHS7kqgBc1pdh8oA17D4X7pzNHe2vtC"

        # 要發送的訊息
        self.msg_list = []

    def append_msg(self, val_list):
        msg = ",".join(val_list)
        msg += "\n"
        self.msg_list.append(msg)

    def send_msg(self):
        if len(self.msg_list) == 1:
            # 只有 table text, 不傳送
            self.msg_list.clear()
            return

        # HTTP 標頭參數與資料
        headers = {"Authorization": "Bearer " + self.token}
        msg = "".join(self.msg_list)
        data = {'message': msg}

        # 以 requests 發送 POST 請求
        requests.post("https://notify-api.line.me/api/notify", headers=headers, data=data)

        self.msg_list.clear()
