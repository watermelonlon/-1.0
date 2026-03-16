import socket
import json
import mysql.connector
from mysql.connector import Error
import traceback


def start_server(host="0.0.0.0", port=12345):
    # 创建数据库连接配置
    db_config = {
        'user': 'root',
        'password': '123456',
        'host': 'localhost',
        'database': 'orders',
    }

    # 检查端口是否可用
    def is_port_available(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            try:
                s.bind((host, port))
                return True
            except OSError:
                return False

    # 如果端口被占用，尝试其他端口
    if not is_port_available(port):
        print(f"端口 {port} 被占用，尝试端口 {port + 1}")
        port += 1

    if not is_port_available(port):
        print(f"端口 {port} 也被占用，请检查并关闭占用端口的程序")
        return

    # 创建服务器 socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 设置端口重用，避免"地址已在使用"错误
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"Server listening on {host}:{port}")
    except OSError as e:
        print(f"无法绑定到端口 {port}: {e}")
        return

    try:
        # 连接到数据库
        db_connection = mysql.connector.connect(**db_config)
        cursor = db_connection.cursor()

        # 初始化累计总价为0
        cumulative_total_price = 0

        print("数据库连接成功！")

        # 初始化数据库表（如果不存在）
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    quantity INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price (
                    id INT PRIMARY KEY DEFAULT 1,
                    totalPrice DECIMAL(10, 2) DEFAULT 0.00
                )
            """)

            # 确保price表有一条记录
            cursor.execute("SELECT COUNT(*) FROM price")
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute("INSERT INTO price (id, totalPrice) VALUES (1, 0)")
                db_connection.commit()

            print("数据库表初始化完成")
        except Exception as e:
            print(f"数据库初始化错误: {e}")

    except Error as e:
        print(f"连接数据库失败: {e}")
        print("请确保:")
        print("1. MySQL服务正在运行")
        print("2. 已创建orders数据库")
        print("3. 数据库用户名和密码正确")
        return

    print("等待客户端连接...")

    try:
        while True:
            try:
                client_socket, client_address = server_socket.accept()
                print(f"收到来自 {client_address} 的连接")

                # 设置接收超时
                client_socket.settimeout(10.0)

                # 接收数据
                data = b""
                try:
                    while True:
                        chunk = client_socket.recv(1024)
                        if not chunk:
                            break
                        data += chunk
                        # 尝试解析JSON，如果成功则停止接收
                        try:
                            json.loads(data.decode('utf-8'))
                            break
                        except:
                            continue
                except socket.timeout:
                    print(f"接收数据超时 from {client_address}")
                    client_socket.close()
                    continue

                if data:
                    try:
                        data_str = data.decode('utf-8').strip()
                        order_data = json.loads(data_str)
                        print("接收到订单数据:")
                        print(json.dumps(order_data, indent=4, ensure_ascii=False))

                        # 检查数据格式
                        if 'totalPrice' not in order_data or 'items' not in order_data:
                            print("数据格式错误，缺少必要字段")
                            client_socket.close()
                            continue

                        try:
                            total_price = float(order_data['totalPrice'])
                            cumulative_total_price += total_price
                        except ValueError:
                            print(f"总价格式错误: {order_data['totalPrice']}")
                            client_socket.close()
                            continue

                        # 查询数据库中的订单商品信息
                        cursor.execute("SELECT name, quantity FROM orders")
                        db_items = cursor.fetchall()

                        # 初始化字典
                        item_dict = {}

                        # 合并数据库中的商品信息到 item_dict
                        for name, quantity in db_items:
                            item_dict[name] = quantity

                        # 处理订单中的商品列表，合并相同名称的商品数量
                        for item in order_data['items']:
                            if 'name' not in item or 'quantity' not in item:
                                print("商品数据格式错误，跳过")
                                continue

                            item_name = item['name']
                            try:
                                item_quantity = int(item['quantity'])
                            except ValueError:
                                print(f"商品数量格式错误: {item['quantity']}")
                                continue

                            if item_name in item_dict:
                                item_dict[item_name] += item_quantity
                            else:
                                item_dict[item_name] = item_quantity

                        # 清空 orders 表
                        truncate_query = "TRUNCATE TABLE orders"
                        cursor.execute(truncate_query)

                        # 更新或插入覆盖后的商品数据
                        for name, quantity in item_dict.items():
                            replace_query = """
                                INSERT INTO orders (name, quantity) 
                                VALUES (%s, %s)
                            """
                            cursor.execute(replace_query, (name, quantity))

                        # 更新总价数据
                        update_query = """UPDATE price SET totalPrice = %s WHERE id = 1"""
                        cursor.execute(update_query, (cumulative_total_price,))

                        # 检查是否更新成功
                        if cursor.rowcount == 0:
                            # 如果没有记录，则插入一条新的记录
                            insert_query = """INSERT INTO price (id, totalPrice) VALUES (1, %s)"""
                            cursor.execute(insert_query, (cumulative_total_price,))

                        db_connection.commit()
                        print("数据更新成功！")
                        print(f"当前累计总价: {cumulative_total_price}")

                        # 发送成功响应给客户端
                        response = json.dumps({"status": "success", "message": "数据接收成功"})
                        client_socket.send(response.encode('utf-8'))

                    except json.JSONDecodeError as e:
                        print(f"JSON解析错误: {e}")
                        print(f"原始数据: {data_str if 'data_str' in locals() else data}")
                        error_response = json.dumps({"status": "error", "message": "JSON格式错误"})
                        client_socket.send(error_response.encode('utf-8'))
                    except Error as e:
                        print(f"数据库错误: {e}")
                        traceback.print_exc()
                        error_response = json.dumps({"status": "error", "message": "数据库错误"})
                        client_socket.send(error_response.encode('utf-8'))

                client_socket.close()

            except KeyboardInterrupt:
                print("\n服务器正在关闭...")
                break
            except Exception as e:
                print(f"处理连接时发生错误: {e}")
                continue

    except KeyboardInterrupt:
        print("\n服务器关闭...")
    finally:
        print("清理资源...")
        if 'cursor' in locals():
            cursor.close()
        if 'db_connection' in locals() and db_connection.is_connected():
            db_connection.close()
        server_socket.close()
        print("服务器已关闭")


if __name__ == "__main__":
    print("=" * 50)
    print("数据接收服务器启动")
    print("=" * 50)
    start_server(port=12346)  # 使用12346端口避免冲突