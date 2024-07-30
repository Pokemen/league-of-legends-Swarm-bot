import base64
import json
import os
import time

import requests
import urllib3

# 禁用 InsecureRequestWarning 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_client_info():
    r = os.popen("wmic PROCESS WHERE name='LeagueClientUx.exe' GET commandline /value")
    text = r.read()
    r.close()
    if len(text) < 50:
        print("获取用户信息失败，请确保已运行游戏和使用管理员身份运行程序！")
        return None, None

    text_items = text.split(" ")

    token = None
    port = None

    for item in text_items:
        item = item.replace('"', '')
        if "--remoting-auth-token" in item:
            index = item.index("=")
            token = item[index + 1:]

        if "--app-port" in item:
            index = item.index("=")
            port = item[index + 1:]

    if token is None:
        print("获取token失败！")
        return None, None

    if port is None:
        print("获取port失败！")
        return None, None

    return token, port

class LCU:
    def __init__(self, token, port):
        self.token = token
        self.port = port
        self.headers = self._build_headers()
        self.url = f"https://127.0.0.1:{port}"

    def _build_headers(self):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Basic " + base64.b64encode(("riot:" + self.token).encode("UTF-8")).decode("UTF-8")
        }
        return headers

    def create_lobby(self):
        """
        创建大厅
        """
        custom1 = {
            "queueId": 1840  # 自定义队列 ID
        }
        url = self.url + "/lol-lobby/v2/lobby"
        time.sleep(3)

        resp = requests.post(url, json=custom1, headers=self.headers, verify=False)
        if not resp.ok:
            print("创建大厅失败！")
            return

        print("大厅创建成功！")
        return resp.json()

    def get_gameflow_phase(self):
        """
        获取游戏状态
        """
        url = self.url + "/lol-gameflow/v1/gameflow-phase"

        resp = requests.get(url, headers=self.headers, verify=False)
        if not resp.ok:
            print("获取游戏状态失败！")
            return

        gameflow_phase = resp.json()
        print("当前游戏状态：", gameflow_phase)
        return gameflow_phase

    def start_matchmaking(self):
        """
        开始匹配
        """
        url = self.url + "/lol-lobby/v2/lobby/matchmaking/search"
        resp = requests.post(url, headers=self.headers, verify=False)
        time.sleep(3)

        # 打印响应状态码和响应内容用于调试
        print(f"响应状态码: {resp.status_code}")
        print(f"响应内容: '{resp.text}'")

        if resp.status_code == 204:
            # 204 No Content 状态码表示成功但没有返回内容
            print("开始匹配成功，但没有返回内容")
            return

        if not resp.ok:
            print("开始匹配失败！")
            return

        try:
            response_json = resp.json()
            print("开始匹配成功！")
            return response_json
        except json.JSONDecodeError:
            print("响应内容无法解析为 JSON")
            return

    def accept_match(self):
        """
        接受匹配
        """
        url = self.url + "/lol-matchmaking/v1/ready-check/accept"
        resp = requests.post(url, headers=self.headers, verify=False)
        time.sleep(3)

        # 打印响应状态码和响应内容用于调试
        print(f"响应状态码: {resp.status_code}")
        print(f"响应内容: '{resp.text}'")

        if resp.status_code == 204:
            # 204 No Content 状态码表示成功但没有返回内容
            print("接受匹配成功，但没有返回内容")
            return

        if not resp.ok:
            print("接受匹配失败！")
            return

        try:
            response_json = resp.json()
            print("接受匹配成功！")
            return response_json
        except json.JSONDecodeError:
            print("响应内容无法解析为 JSON")
            return

    def play_again(self):
        """
        再次游戏
        """
        url = self.url + "/lol-lobby/v2/play-again"
        resp = requests.post(url, headers=self.headers, verify=False)
        if not resp.ok:
            print("再次游戏失败！")
            return

        print("再次游戏成功！")
        time.sleep(3)
        return

    def exit_lobby(self):
        """
        退出大厅
        """
        url = self.url + "/lol-lobby/v2/lobby"  # 退出大厅的 API 端点

        try:
            resp = requests.delete(url, headers=self.headers, verify=False)
            resp.raise_for_status()  # 如果响应状态码不是 200，将引发 HTTPError

            # 处理响应数据
            if resp.status_code == 204:  # HTTP 204 No Content 表示成功退出
                print("成功退出大厅")
            else:
                print("退出大厅失败，状态码:", resp.status_code)
        except requests.exceptions.RequestException as e:
            print(f"退出大厅失败: {e}")

if __name__ == "__main__":
    token, port = get_client_info()

    # 输出 token 和 port
    if token and port:
        print(f"Token: {token}")
        print(f"Port: {port}")

        lcu = LCU(token, port)
        # 创建大厅
        #lcu.create_lobby()
        time.sleep(2)
        # 获取游戏状态
        #lcu.get_gameflow_phase()
        # 示例操作
        #lcu.start_matchmaking()
        #lcu.accept_match()
        lcu.play_again()
