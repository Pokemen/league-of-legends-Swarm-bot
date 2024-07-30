import time
import mouse
import cv2 as cv
import numpy as np
import os
import pyautogui
import requests
import utils
import pydirectinput


def get_game_data():
    port = 2999
    base_url = f'https://127.0.0.1:{port}'

    headers = {
        'Content-Type': 'application/json'
    }

    # 发送请求获取游戏状态
    response = requests.get(f'{base_url}/liveclientdata/allgamedata', headers=headers, verify=False)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch game data: {response.status_code} - {response.reason}")
        return None




def split_image_into_three(img):
    # 获取图像的高度和宽度
    height, width = img.shape[:2]
    print(height, width)

    # 计算每个剪裁部分的高度
    slice_height = height // 3
    print(slice_height - 85, slice_height + 90)
    print(width // 3)

    # 剪裁图像的三个部分
    img_part1 = img[270:460, 490:700]
    img_part2 = img[270:460, 850:1060]
    img_part3 = img[270:460, 1220:1430]

    return img_part1, img_part2, img_part3

def load_images_from_folder(folder):
    images = {}
    for filename in os.listdir(folder):
        if filename.endswith(('.jpg', '.png')):
            img_path = os.path.join(folder, filename)
            img = cv.imread(img_path, cv.IMREAD_UNCHANGED)
            if img is not None:
                images[filename] = img
            else:
                print(f"Warning: Cannot read image: {img_path}")
    return images

def process_image_pair(haystack_img, needle_img):
    image_gray = cv.cvtColor(haystack_img, cv.COLOR_BGR2GRAY)
    template_gray = cv.cvtColor(needle_img, cv.COLOR_BGR2GRAY)
    result = cv.matchTemplate(image_gray, template_gray, cv.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv.minMaxLoc(result)
    return max_val

def find_best_match(haystack_images, needle_img):
    best_match = None
    best_val = -1

    for filename, img in haystack_images.items():
        max_val = process_image_pair(img, needle_img)
        if max_val > best_val:
            best_val = max_val
            best_match = filename

    if best_val >= 0.8:
        return best_match, best_val
    else:
        return None, None

def find_best_match_value(best_match1, best_match2, best_match3):
    def assign_value(filename):
        # 根据文件名或其他规则分配图片价值
        value_map = {
            '1.jpg': 10,
            '2.jpg': 20,
            '3.jpg': 40,
            '4.jpg': 50,
            '5.jpg': 50,
            '6.jpg': 40,
            '7.jpg': 40,
            '8.jpg': 50,
            '9.jpg': 60,
            '10.jpg': 50,
            '11.jpg': 10,
            '12.jpg': 85,
            '13.jpg': 50,
            '14.jpg': 50,
            '15.jpg': 50,
            '16.jpg': 50,
            '17.jpg': 50,
            '18.jpg': 80,
            '19.jpg': 80,
            '20.jpg': 100, # 木枷
            '21.jpg': 95, # 电刀
            '22.jpg': 10,
            '23.jpg': 90, # 最大生命值
            '24.jpg': 60,
            '25.jpg': 60,
            '26.jpg': 10,
            '27.jpg': 40,
            '28.jpg': 60,
            '29.jpg': 40,
            '30.jpg': 40,
            '31.jpg': 50,
            '32.jpg': 60,
            '33.jpg': 60,
        }
        return value_map.get(filename, 0)

    # 检查所有 best_match 是否都是空
    if not best_match1 and not best_match2 and not best_match3:
        return None, None

    value1 = assign_value(best_match1) if best_match1 else 0
    value2 = assign_value(best_match2) if best_match2 else 0
    value3 = assign_value(best_match3) if best_match3 else 0

    if value1 >= value2 and value1 >= value3:
        return best_match1, "best_match1"
    elif value2 >= value1 and value2 >= value3:
        return best_match2, "best_match2"
    else:
        return best_match3, "best_match3"

def leveling_loop():
    """Loop that runs the correct function based on the phase of the League Client, continuously starts games"""
    # 连接到 League Client Update (LCU) 服务
    token, port = utils.get_client_info()
    lcu = utils.LCU(token, port)
    matchmaking_count = 0
    while True:
        # 在循环中调用异步方法
        phase = lcu.get_gameflow_phase()
        match phase:
            case 'None':
                lcu.create_lobby()
            case 'Lobby':
                matchmaking_count += 1  # 增加计数器
                lcu.start_matchmaking()

                # 如果计数器达到了 20，则执行 lcu.exit_lobby()，然后重置计数器
                if matchmaking_count >= 10:
                    lcu.exit_lobby()
            case 'ReadyCheck':
                lcu.accept_match()
                matchmaking_count = 0
            case 'InProgress':
                # 处理游戏进行中的逻辑
                game_in()
            case 'EndOfGame':
                lcu.play_again()

        time.sleep(1)



def game_in():
    # 加载模板图片
    token, port = utils.get_client_info()
    lcu = utils.LCU(token, port)
    haystack_dir = '/picture'  # 替换为您的图像文件夹路径
    # 初始化图片库
    haystack_images = load_images_from_folder(haystack_dir)

    last_health_check_time = time.time()  # 记录上一次检查健康的时间
    health_check_interval = 8  # 健康检查的间隔时间（秒）

    while True:
        phase = lcu.get_gameflow_phase()
        if phase == 'EndOfGame':
            break

        # 截图并读取到 OpenCV 图像中
        time.sleep(1)
        screenshot = pyautogui.screenshot()
        screenshot = cv.cvtColor(np.array(screenshot), cv.COLOR_RGB2BGR)

        # 分割截图
        part1, part2, part3 = split_image_into_three(screenshot)

        # 进行模板匹配
        best_match1, _ = find_best_match(haystack_images, part1)
        best_match2, _ = find_best_match(haystack_images, part2)
        best_match3, _ = find_best_match(haystack_images, part3)
        best_match, best_match_area = find_best_match_value(best_match1, best_match2, best_match3)
        print("价值最高的图片是:", best_match)
        print("该图片属于区域:", best_match_area)

        # 将鼠标移动到最高价值区域并点击
        if best_match_area == "best_match1":
            pyautogui.moveTo(595, 365)  # 移动到第一个区域的中心
        elif best_match_area == "best_match2":
            pyautogui.moveTo(955, 365)  # 移动到第二个区域的中心
        elif best_match_area == "best_match3":
            pyautogui.moveTo(1325, 365)  # 移动到第三个区域的中心

        if best_match_area:
            mouse.click()

        # 获取游戏数据
        game_data = get_game_data()
        if game_data is None:
            print("游戏数据无法获取")
            break  # 跳过当前循环的其余部分
        else:
            maxHealth = game_data['activePlayer']['championStats']['maxHealth']
            currentHealth = game_data['activePlayer']['championStats']['currentHealth']
            L_Health = int(maxHealth * 0.4)  # 健康阈值设定为40%
            # 判断是否执行技能按键
            current_time = time.time()
            if current_time - last_health_check_time >= health_check_interval:
                pydirectinput.press('e')
                last_health_check_time = current_time
            if L_Health >= currentHealth:
                pydirectinput.press('r')


            print(f"maxHealth: {game_data['activePlayer']['championStats']['maxHealth']}")
            print(f"currentHealth: {game_data['activePlayer']['championStats']['currentHealth']}")



        # 将三个部分组合成一个窗口显示
        combined_img = np.hstack((part1, part2, part3))
        cv.imshow('Combined Parts', combined_img)

        if cv.waitKey(1) == ord('q'):
            break

    cv.destroyAllWindows()

if __name__ == "__main__":
    leveling_loop()



