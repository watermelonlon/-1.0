import NDIlib as ndi
import numpy as np
import cv2

# 本代码用于展示如何截取NDI视频流
# Python版本为3.10
# 其他库安装命令：
# pip install ndi-python opencv-python numpy

def main():
    # 1. 初始化 NDI
    if not ndi.initialize():
        print("无法初始化 NDI.")
        return 0

    # 2. 创建查找器 (用于寻找网络中的 NDI 源)
    ndi_find = ndi.find_create_v2()

    if ndi_find is None:
        print("无法创建 NDI 查找器.")
        return 0

    sources = []
    while not sources:
        print("正在寻找 NDI 源...")
        ndi.find_wait_for_sources(ndi_find, 1000)
        sources = ndi.find_get_current_sources(ndi_find)

    # 打印找到的源
    print(f"找到 {len(sources)} 个 NDI 源:")
    for i, s in enumerate(sources):
        print(f"{i}: {s.ndi_name}")

    # 3. 连接到第一个找到的源 (通常就是你的 Unity 源)
    # 如果你有多个源，可以通过判断 s.ndi_name 来选择 'UnityCam'
    target_source = sources[0]
    print(f"正在连接到: {target_source.ndi_name}")

    ndi_recv = ndi.recv_create_v3()
    if ndi_recv is None:
        print("无法创建 NDI 接收器.")
        return 0

    ndi.recv_connect(ndi_recv, target_source)

    # 4. 循环读取帧
    cv2.namedWindow("Unity NDI Stream", cv2.WINDOW_NORMAL)

    while True:
        t, v, a, m = ndi.recv_capture_v2(ndi_recv, 5000)

        if t == ndi.FRAME_TYPE_VIDEO:

            # 获取视频帧数据
            # v.data 是指向内存的指针，我们需要构建 numpy array
            frame = np.copy(np.frombuffer(v.data, dtype=np.uint8))

            # 根据分辨率重塑数组 (Height, Width, Channels)
            # NDI 为了节省带宽，默认发送的是 UYVY (YUV 4:2:2) 格式
            frame = frame.reshape((v.yres, v.xres, 2))

            # 如果需要，丢弃 Alpha 通道转换为 BGR (OpenCV 标准)
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_UYVY)

            cv2.imshow("Unity NDI Stream", frame_bgr)

            # 释放 NDI 帧内存，非常重要！
            ndi.recv_free_video_v2(ndi_recv, v)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 5. 清理资源
    ndi.recv_destroy(ndi_recv)
    ndi.find_destroy(ndi_find)
    ndi.destroy()
    cv2.destroyAllWindows()
    return None


if __name__ == "__main__":
    main()