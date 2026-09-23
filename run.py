"""启动脚本：自动挑选可用端口（优先 8000，被占用则用 8001/8002...）。

用法：
    python run.py                      本机访问（127.0.0.1，自动挑端口）
    python run.py --lan                局域网访问（0.0.0.0，同 WiFi 的同事/同学可打开）
    python run.py --host 0.0.0.0 --port 8080   手动指定

环境变量（云部署平台会自动注入，优先级低于命令行参数）：
    HOST=0.0.0.0   监听地址
    PORT=10000     监听端口

或在项目根目录双击 run.bat
"""
import os
import socket
import sys

try:
    import uvicorn
except ImportError:
    print("缺少依赖，请先执行： python -m pip install -r requirements.txt")
    sys.exit(1)


def parse_args():
    """手写的极简参数解析，避免为两个开关引入 argparse 之外的依赖"""
    host, port, lan = None, None, False
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--lan":
            lan = True
        elif a == "--host" and i + 1 < len(argv):
            host = argv[i + 1]
            i += 1
        elif a == "--port" and i + 1 < len(argv):
            port = int(argv[i + 1])
            i += 1
        elif a.startswith("--host="):
            host = a.split("=", 1)[1]
        elif a.startswith("--port="):
            port = int(a.split("=", 1)[1])
        i += 1
    return host, port, lan


def is_free(host: str, port: int) -> bool:
    s = socket.socket()
    try:
        s.bind((host, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def pick_port(host: str) -> int:
    """0.0.0.0 与具体 IP 的占用情况一致，用 0.0.0.0 探测最保险"""
    probe = "0.0.0.0" if host in ("0.0.0.0", "") else host
    for p in range(8000, 8010):
        if is_free(probe, p):
            return p
    return 8000


def lan_ips():
    """列出本机在局域网里的 IP，方便把地址发给别人"""
    ips = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))     # 不会真的发包，只为拿到出口网卡 IP
        ips.append(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip not in ips and not ip.startswith("127."):
                ips.append(ip)
    except Exception:
        pass
    return ips


def main():
    arg_host, arg_port, lan = parse_args()

    # 优先级：命令行参数 > 环境变量 > 默认值
    host = arg_host or os.getenv("HOST") or ("0.0.0.0" if lan else "127.0.0.1")
    port = arg_port or (int(os.getenv("PORT")) if os.getenv("PORT") else pick_port(host))

    print("=" * 52)
    print("  PyOJ 耘码启动中...")
    if host == "0.0.0.0":
        print(f"  本机打开：     http://127.0.0.1:{port}")
        for ip in lan_ips():
            print(f"  局域网其他人： http://{ip}:{port}")
        print("  （若别人打不开，多半是本机防火墙拦了，见 README-部署.md）")
    else:
        print(f"  请在浏览器打开： http://{host}:{port}")
    print(f"  停止服务：在此窗口按 Ctrl + C")
    print("=" * 52)

    uvicorn.run("main:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
