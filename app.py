from flask import Flask, request, render_template, redirect, flash, url_for, session, jsonify
import threading
import socket
import pickle
import struct
import cv2
import numpy as np
from queue import Queue
import time
from datetime import datetime

app = Flask(__name__)

# 设置 secret_key
app.secret_key = 'your_unique_secret_key_here'

# 在app.secret_key后添加
app.secret_key = 'your_unique_secret_key_here'
app.config['SESSION_PERMANENT'] = False  # 设置为False，浏览器关闭时过期
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30分钟过期（即使浏览器未关闭）
app.config['SESSION_COOKIE_NAME'] = 'flask_session'
app.config['SESSION_COOKIE_SECURE'] = False  # 开发环境设为False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


@app.route('/clear-session-silent', methods=['POST'])
def clear_session_silent():
    """静默清除会话（无重定向）"""
    session.clear()
    return '', 204  # 返回空响应


# 内存存储用户数据
app.config['TEMP_USERS'] = {
    'admin': {'password': '123456', 'id': 1, 'created_at': '2025-01-01 00:00:00'},
    'test': {'password': 'test123', 'id': 2, 'created_at': '2025-01-01 00:00:00'}
}

# 模拟订单数据
MOCK_ITEMS = [
    {'name': '宫保鸡丁', 'total_quantity': 61},
    {'name': '清蒸鲈鱼', 'total_quantity': 92},
    {'name': '鱼香肉丝', 'total_quantity': 62},
    {'name': '麻婆豆腐', 'total_quantity': 51},
    {'name': '酸辣肉丝', 'total_quantity': 42}
]

MOCK_TOTAL_PRICE = {'totalPrice': 156.80}

# 全局队列用于存储接收到的帧
frame_queue = Queue(maxsize=10)
# 线程启动标志，确保只启动一次
video_thread_started = False
video_thread_lock = threading.Lock()


# def receive_frames():
#     server_ip = "192.168.43.181"  # 替换为服务端的 IP 地址
#     server_port = 8888
#
#     print(f"尝试连接视频服务: {server_ip}:{server_port}")
#
#     try:
#         client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         client_socket.settimeout(10)
#         client_socket.connect((server_ip, server_port))
#         print(f"已连接到服务端：{server_ip}:{server_port}")
#
#         data_buffer = b""
#
#         try:
#             while True:
#                 while len(data_buffer) < 4:
#                     packet = client_socket.recv(4096)
#                     if not packet:
#                         print("服务端断开连接。000")
#                         return
#                     data_buffer += packet
#
#                 packed_msg_size = data_buffer[:4]
#                 data_buffer = data_buffer[4:]
#                 msg_size = struct.unpack("!I", packed_msg_size)[0]
#
#                 while len(data_buffer) < msg_size:
#                     packet = client_socket.recv(4096)
#                     if not packet:
#                         print("服务端断开连接。111")
#                         return
#                     data_buffer += packet
#
#                 frame_data = data_buffer[:msg_size]
#                 data_buffer = data_buffer[msg_size:]
#
#                 try:
#                     frame_bytes = pickle.loads(frame_data)
#                     frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
#                     if frame is not None and not frame_queue.full():
#                         frame_queue.put_nowait(frame)
#                 except Exception as e:
#                     print(f"数据解析失败：{e}")
#                     continue
#
#         except (ConnectionResetError, BrokenPipeError):
#             print("服务端断开连接")
#         except socket.timeout:
#             print("接收超时")
#         except Exception as e:
#             print(f"视频接收错误: {e}")
#
#     except socket.timeout:
#         print(f"连接视频服务超时: {server_ip}:{server_port}")
#         print("启动模拟视频流...")
#         start_mock_video_stream()
#     except ConnectionRefusedError:
#         print(f"连接被拒绝: {server_ip}:{server_port}")
#         print("启动模拟视频流...")
#         start_mock_video_stream()
#     except Exception as e:
#         print(f"连接视频服务失败: {e}")
#         print("启动模拟视频流...")
#         start_mock_video_stream()
#     finally:
#         if 'client_socket' in locals():
#             client_socket.close()

def receive_frames():
    """接收视频帧（替换为视频文件video2.mp4）"""
    video_path = "video2.mp4"  # 确保文件路径正确
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("无法打开视频文件")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("视频播放完毕或出现错误")
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 重置视频到开头
            continue

        if frame is not None and not frame_queue.full():
            frame_queue.put_nowait(frame)

        # 增加延迟以实现慢速播放
        time.sleep(0.05)  # 根据需要调整延迟时间

    cap.release()

def start_mock_video_stream():
    """启动模拟视频流"""
    threading.Thread(target=generate_mock_frames, daemon=True).start()


def generate_mock_frames():
    """生成模拟视频帧用于测试"""
    print("模拟视频流已启动")
    frame_count = 0
    while True:
        try:
            # 创建一个渐变色背景
            frame = np.zeros((480, 640, 3), dtype=np.uint8)

            # 创建渐变色
            for i in range(480):
                color_value = int((i / 480) * 255)
                frame[i, :, 1] = color_value  # 绿色通道

            # 添加一些动态文字
            cv2.putText(frame, "模拟视频流", (50, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
            cv2.putText(frame, f"帧数: {frame_count}", (50, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            cv2.putText(frame, "等待连接192.168.43.181:8888", (50, 250),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # 添加一个移动的圆形
            center_x = 320 + int(200 * np.sin(frame_count * 0.1))
            center_y = 240 + int(150 * np.cos(frame_count * 0.07))
            cv2.circle(frame, (center_x, center_y), 30, (0, 0, 255), -1)

            if not frame_queue.full():
                frame_queue.put_nowait(frame)

            frame_count += 1
            time.sleep(0.033)  # 约30帧/秒
        except Exception as e:
            print(f"模拟视频流错误: {e}")
            time.sleep(1)


@app.before_request
def initialize():
    """初始化视频接收线程（只启动一次）"""
    global video_thread_started

    with video_thread_lock:
        if not video_thread_started:
            video_thread_started = True
            print("启动视频接收线程...")
            threading.Thread(target=receive_frames, daemon=True).start()


@app.route('/')
def home():
    """根路由重定向到登录页"""
    return redirect(url_for('login'))


@app.route('/index.html')
def home_index():
    """主页"""
    # 检查是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 重定向到detect页面（检测页面）
    return redirect(url_for('index'))


@app.route('/video_feed')
def video_feed():
    def generate_frames():
        while True:
            try:
                if not frame_queue.empty():
                    frame = frame_queue.get()
                    ret, jpeg = cv2.imencode('.jpg', frame)
                    if ret:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                else:
                    # 如果队列为空，等待一小段时间
                    time.sleep(0.01)
            except Exception as e:
                print(f"视频流生成错误: {e}")
                time.sleep(0.1)

    return app.response_class(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/detect.html')
def index():
    """检测页面 - 显示订单信息"""
    # 检查是否已登录
    if 'user_id' not in session:
        flash('请先登录', 'warning')
        return redirect(url_for('login'))

    # 获取用户名
    username = session.get('username', '用户')

    return render_template('detect.html',
                           items=MOCK_ITEMS,
                           total_price=MOCK_TOTAL_PRICE,
                           username=username)


@app.route('/login.html', methods=["GET", "POST"])
def login():
    """登录页面 - 每次访问都强制重新登录"""
    # 关键修改：每次访问登录页都清除会话
    session.clear()
    print("访问登录页，已清除会话，需要重新登录")

    # 如果通过POST提交表单，处理登录逻辑
    if request.method == "POST":
        # 获取表单数据
        username = request.form.get("user")
        password = request.form.get("pwd")
        enroll_username = request.form.get("username")
        enroll_password = request.form.get("password")

        print(f"登录尝试: username={username}, enroll_username={enroll_username}")

        # 注册逻辑
        if enroll_username and enroll_username.strip() and enroll_password:
            if enroll_username not in app.config['TEMP_USERS']:
                # 生成用户ID
                user_id = len(app.config['TEMP_USERS']) + 1
                app.config['TEMP_USERS'][enroll_username] = {
                    'id': user_id,
                    'password': enroll_password,
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                flash('注册成功!', 'success')
                print(f"用户注册成功: {enroll_username}, ID: {user_id}")
                # 自动登录新注册用户
                session['user_id'] = user_id
                session['username'] = enroll_username
                return redirect(url_for('home_index'))
            else:
                flash('用户名已经存在！', 'danger')

        # 登录验证
        if username and password:
            # 检查临时用户
            if username in app.config['TEMP_USERS']:
                user_info = app.config['TEMP_USERS'][username]
                if user_info['password'] == password:
                    session['user_id'] = user_info['id']
                    session['username'] = username
                    flash('登录成功!', 'success')
                    print(f"用户登录成功: {username}")
                    return redirect(url_for('home_index'))

            # 默认测试账户
            if username == "admin" and password == "123456":
                session['user_id'] = 999
                session['username'] = "admin"
                flash('管理员登录成功!', 'success')
                print(f"管理员登录成功: {username}")
                return redirect(url_for('home_index'))

            if username == "test" and password == "test123":
                session['user_id'] = 998
                session['username'] = "test"
                flash('测试用户登录成功!', 'success')
                print(f"测试用户登录成功: {username}")
                return redirect(url_for('home_index'))

            flash('用户名或密码错误!', 'danger')

    # 如果是GET请求或登录失败，显示登录页面
    return render_template('login.html')



@app.route('/moudle.html')
def moudle():
    """模块页面"""
    # 检查是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('moudle.html', username=session.get('username'))


@app.route('/base.html')
def base():
    """基础页面"""
    # 检查是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 直接重定向到detect页面
    return redirect(url_for('index'))


@app.route('/elevator.html')
def elevator():
    """电梯页面"""
    # 检查是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('elevator.html', username=session.get('username'))


@app.route('/voice.html')
def voice():
    """语音页面"""
    # 检查是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # 添加默认值，避免模板错误
    return render_template('voice.html',
                           received_messages=[],
                           username=session.get('username'))


@app.route('/person.html')
def person():
    """个人页面"""
    # 检查是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('person.html', username=session.get('username'))


@app.route('/logout')
def logout():
    """退出登录"""
    username = session.get('username', '未知用户')
    session.clear()
    flash(f'用户 {username} 已退出登录', 'info')
    return redirect(url_for('login'))


@app.route('/api/orders', methods=['GET'])
def get_orders():
    """获取订单数据的API接口"""
    try:
        return jsonify({
            'success': True,
            'items': MOCK_ITEMS,
            'total_price': MOCK_TOTAL_PRICE['totalPrice']
        })
    except Exception as e:
        print(f"API错误: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/debug/users')
def debug_users():
    """调试页面：查看当前存储的用户"""
    if 'user_id' not in session:
        return "请先登录"

    users_info = []
    for username, info in app.config['TEMP_USERS'].items():
        users_info.append({
            'username': username,
            'id': info['id'],
            'created_at': info.get('created_at', '未知')
        })

    return jsonify({
        'current_user': {
            'id': session.get('user_id'),
            'username': session.get('username')
        },
        'total_users': len(users_info),
        'users': users_info
    })


def check_port(port):
    """检查端口是否被占用"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        try:
            s.connect(('127.0.0.1', port))
            return True
        except:
            return False


if __name__ == '__main__':
    # 检查端口是否被占用
    port = 5000
    if check_port(port):
        port = 5001
        print(f"端口5000被占用，使用端口{port}")

    print("=" * 60)
    print(f"Flask应用运行在: http://127.0.0.1:{port}")
    print("=" * 60)
    print("使用说明:")
    print(f"1. 访问 http://localhost:{port} 打开登录页面")
    print(f"2. 访问 http://localhost:{port}/index.html 打开主页")
    print(f"3. 访问 http://localhost:{port}/detect.html 打开检测页面")
    print(f"4. 访问 http://localhost:{port}/video_feed 查看视频流")
    print(f"5. 访问 http://localhost:{port}/api/orders 获取订单数据API")
    print("=" * 60)
    print("测试账户:")
    print("  用户名: admin, 密码: 123456")
    print("  用户名: test, 密码: test123")
    print("=" * 60)

    app.run(debug=True, port=port, host='0.0.0.0')