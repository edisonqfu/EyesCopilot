import base64
import json
import openai
import time
import cv2


from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.ocr.v20181119 import ocr_client, models

# 腾讯云的基础配置
# 替换为自己的腾讯云的SecretId和SecretKey信息,需要替换成自己的id
tencent_secret_id = "*******"
tencent_secret_key = "*******"

# 初始化认证信息
cred = credential.Credential(tencent_secret_id, tencent_secret_key)

# 初始化腾讯云服务配置信息
http_profile = HttpProfile()
http_profile.endpoint = "ocr.tencentcloudapi.com"
http_profile.reqTimeout=30

client_profile = ClientProfile()
client_profile.httpProfile = http_profile

# 初始化腾讯云 OCR 客户端
client = ocr_client.OcrClient(cred, "ap-guangzhou", client_profile)


# OPEN AI 的基础配置
openai.api_key = "**************"

# 替换成您想要使用的模型 ID gpt-3.5-turbo
model_id = "gpt-3.5-turbo"

# 本程序的基础配置
# IP摄像机的URL，可替换为自己的IP摄像头地址
url = 'http://192.168.0.111:81/stream'
# 创建VideoCapture对象
cap = cv2.VideoCapture(url)
# root=tk.Tk()

# 初始化对话历史
conversation_history = []

# 定义函数：导出图片到项目
def save_image(frame):
    cv2.imwrite("Pic.png", frame)



# 定义函数：与 GPT-3.5 进行一问一答对话
def ask(question):
    conversation={
        "role":"user",
        "content":question
    }
    conversation_history.append(conversation)

    # print(conversation_history)
    # 设置代理服务器，根据自己的科学上网设置
    openai.proxy = "http://127.0.0.1:7890"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation_history
    )

    # print(response)

    answer = response.choices[0].message.content
    # print(answer)
    return answer


# 检查是否成功连接到摄像头
if not cap.isOpened():
    print("无法连接到EyeCopilote")
    exit()

# 循环读取视频帧并开启主程序
while True:
    ret, frame = cap.read()
    # 检查是否成功获取帧
    if not ret:
        print("无法获取帧")
        break
    # 显示帧
    cv2.imshow('EyesCopilot', frame)

    # 让用户选择模式
    select_or_question = input("EyesCopilot:请直接输入您的问题(或按1来学习,exit来退出)").replace("\n", "")
    if select_or_question=="1":
        save_image(frame)
        time.sleep(2)
        # 打开并读取图片文件
        with open("Pic.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        # print(encoded_string)
        # 构造请求对象
        req = models.GeneralBasicOCRRequest()
        # 设置请求参数
        params = {
            "ImageBase64": encoded_string.decode("utf-8"),
            "LanguageType": "zh",
        }
        req.from_json_string(json.dumps(params))
        # 发送请求并获取响应
        resp = client.GeneralBasicOCR(req)

        text_content=""
        # 解析响应数据
        for text in resp.TextDetections:
            # print(text.DetectedText, text.Confidence)
            text_content=text_content+text.DetectedText+";"
  
        answer = ask("请帮我记住以下知识："+text_content)
        print("EyesCopilot的回答是：", answer)
        conversation = {
            "role": "assistant",
            "content": answer
        }
        conversation_history.append(conversation)
    else:
        question = select_or_question
        if question == "exit":
            break
        answer = ask(question)
        print("edison的回答是：", answer)
        conversation={
            "role":"assistant",
            "content":answer
        }
        conversation_history.append(conversation)
        time.sleep(1)

# 释放资源
cap.release()
cv2.destroyAllWindows()
