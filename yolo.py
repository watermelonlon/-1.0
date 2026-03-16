import cv2
import numpy as np

# Load YOLO model and configuration files
net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

# 读取视频流
cap = cv2.VideoCapture("video.mp4")

# 获取视频帧率
fps = cap.get(cv2.CAP_PROP_FPS)
# 加快播放速度，加快倍数
speed_up_factor = 10  # 设置为 2 表示加快 2 倍
frame_delay = int(1000 / (fps * speed_up_factor))

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    height, width, channels = frame.shape
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outputs = net.forward(output_layers)

    # 处理检测结果 (位置, 置信度)
    for output in outputs:
        for detect in output:
            scores = detect[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:  # 设置置信度阈值
                # 计算边框位置
                center_x = int(detect[0] * width)
                center_y = int(detect[1] * height)
                w = int(detect[2] * width)
                h = int(detect[3] * height)

                # 绘制矩形
                cv2.rectangle(frame, (center_x, center_y), (center_x + w, center_y + h), (255, 0, 0), 2)

    # cv2.imshow("Frame", frame)
    #
    # # 根据加快倍数调整每帧的延迟
    # if cv2.waitKey(frame_delay) & 0xFF == ord('q'):
    #     break
    cv2.imshow("Frame", frame)
# 使用小的延迟值
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()