from . import Scaffolding, F_Server, F_Client
import atexit
import json
import os.path
import subprocess
import random
import socket
import asyncio


class EasyTier:
    def __init__(self):
        self.process = None

    def launch_easytier(self, et_core_path: str, code: str, become_host: bool = False, server_port: int | str = 3939, nodes: list | None = None, minecraft_port: int | str = 25565):
        if not Scaffolding.validate_code(code):
            return
        nodes = [
            "tcp://public.easytier.cn:11010"
        ] if nodes is None else nodes
        et_params = [
            et_core_path, "--no-tun", "--multi-thread", "--latency-first", "--enable-kcp-proxy", "-d",
            "--network-name", f"scaffolding-mc-{code[2:11]}",
            "--network-secret", code[12:21]
        ]
        if become_host:
            et_params.append("--hostname")
            et_params.append(f"scaffolding-mc-server-{server_port}")
            et_params.append(f"--tcp-whitelist")
            et_params.append(str(server_port))
            et_params.append(str(minecraft_port))
        else:
            et_params.append("--tcp-whitelist=0")
            et_params.append("--udp-whitelist=0")
        for a_node in nodes:
            et_params.append("-p")
            et_params.append(a_node)
        # EasyTier, Launch!
        self.process = subprocess.Popen(et_params, encoding="utf-8")
        # 注册清理函数，确保程序退出时终止子进程
        atexit.register(self.terminate)

    def terminate(self):
        if self.process and self.process.poll() is None:
            # 如果进程还在运行，则终止它
            self.process.terminate()  # 发送终止信号
            # 等待一段时间，如果进程仍然不退出，则强制杀死
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

    def wait(self, timeout=None):
        if self.process:
            try:
                return self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                return None
        return None

    def is_running(self):
        return self.process and self.process.poll() is None

    @staticmethod
    def easytier_peer(et_cli_path: str) -> list:
        result = subprocess.run([et_cli_path, "-o", "json", "peer"], encoding="utf-8", capture_output=True, text=True)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return []

    @staticmethod
    def bind_address(et_cli_path: str, local_address: str, virtual_address: str):
        subprocess.run([et_cli_path, "port-forward", "add", "tcp", local_address, virtual_address])


def get_available_port():
    """简单获取可用随机端口"""
    while True:
        port = random.randint(1025, 65535)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("", port))
                return port
        except OSError:
            continue


def create_room(easytier_path: str):
    easytier_path = easytier_path.replace("\\", "/").strip("/")
    et_cli_path = ""
    et_core_path = ""
    if os.path.isdir(easytier_path):
        for et_name in os.listdir(easytier_path):
            if "cli" in et_name:
                et_cli_path = f"{easytier_path}/{et_name}"
            elif "core" in et_name:
                et_core_path = f"{easytier_path}/{et_name}"
    if et_cli_path == "" or et_core_path == "":
        return
    easytier = EasyTier()
    server_port = get_available_port()
    code = Scaffolding.generate_code()
    print("房间码:", code)
    easytier_id = 0
    easytier.launch_easytier(et_core_path, code, True, server_port)
    for get_peer in easytier.easytier_peer(et_cli_path):
        if get_peer.get("hostname") == f"scaffolding-mc-server-{server_port}":
            easytier_id = get_peer.get("id")
    # easytier.bind_address(et_cli_path, f"127.0.0.1:{server_port}", f"{virtual_host}:{server_port}")
    machine_id = Scaffolding.machine_id()
    asyncio.run(start_server(machine_id, easytier_id, "AEAE", server_port=server_port))


async def start_server(machine_id: str, easytier_id: int | str, player_name: str = "", server_host: str = "0.0.0.0", server_port: int = 3939, minecraft_port: int | str = 25565):
    async with F_Server.AsyncFloroldingServer(machine_id, easytier_id, player_name, server_host, server_port, minecraft_port) as server:
        await server.start()


def join_room(easytier_path: str, code: str):
    if not Scaffolding.validate_code(code):
        return
    easytier_path = easytier_path.replace("\\", "/").strip("/")
    et_cli_path = ""
    et_core_path = ""
    if os.path.isdir(easytier_path):
        for et_name in os.listdir(easytier_path):
            if "cli" in et_name:
                et_cli_path = f"{easytier_path}/{et_name}"
            elif "core" in et_name:
                et_core_path = f"{easytier_path}/{et_name}"
    if et_cli_path == "" or et_core_path == "":
        return
    easytier = EasyTier()
    easytier.launch_easytier(et_core_path, code)
    import time
    time.sleep(20)
    virtual_ip = ""
    server_port = 0
    easytier_id = 0
    peer = easytier.easytier_peer(et_cli_path)
    print(peer)
    for get_peer in peer:
        if get_peer.get("hostname").startswith("scaffolding-mc-server-"):
            server_port = int(get_peer.get("hostname").replace("scaffolding-mc-server-", ""))
            virtual_ip = get_peer.get("ipv4")
        if get_peer.get("cost") == "Local":
            easytier_id = get_peer.get("id")
    if virtual_ip == "" or server_port == 0:
        print("未找到联机中心")
        return
    get_port = get_available_port()
    easytier.bind_address(et_cli_path, f"127.0.0.1:{get_port}", f"{virtual_ip}:{server_port}")
    # time.sleep(5)
    machine_id = Scaffolding.machine_id()
    # client = F_Client.AsyncFloroldingClient(machine_id, easytier_id, "AE233", server_port=get_port)
    # asyncio.run(client.connect())
    asyncio.run(main(machine_id, easytier_id, get_port))


async def main(machine_id, easytier_id, get_port):
    async with F_Client.AsyncFloroldingClient(machine_id, easytier_id, "AE233", server_port=get_port) as client:
        # 等待连接稳定
        await asyncio.sleep(5)
        await client.c_protocols()
        # 执行所有操作
        for _ in range(10):
            # await client.c_protocols()
            # await client.c_ping(b"Test connect")
            await client.c_server_port()
            # await client.c_player_profiles_list()
        await client.c_player_profiles_list()

        print("获取端口错误次数:", client.error_num)
