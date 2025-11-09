import requests
from urllib3.exceptions import InsecureRequestWarning
import warnings


def get_easytier_version_list(get_github: bool =False, github_proxy: str ="") -> dict:
    r"""
    获取EasyTier的下载地址
    :param get_github: 是否从从GitHub获取, 默认从EasyTier节点状态中获取版本号拼接
    :param github_proxy: 能镜像api.github.com的镜像源
    :return: {"系统名": {"架构": "完整下载地址"}}
    """
    easytier_version = get_easytier_version(get_github, github_proxy)
    version_list = {
        "Windows": {
            "x86_64" : f"https://github.com/EasyTier/EasyTier/releases/download/v{easytier_version}/easytier-windows-x86_64-v{easytier_version}.zip",
            "arm64": f"https://github.com/EasyTier/EasyTier/releases/download/v{easytier_version}/easytier-windows-arm64-v{easytier_version}.zip"
        },
        "Linux": {
            "x86_64": f"https://github.com/EasyTier/EasyTier/releases/download/v{easytier_version}/easytier-linux-x86_64-v{easytier_version}.zip",
            "aarch64": f"https://github.com/EasyTier/EasyTier/releases/download/v{easytier_version}/easytier-linux-aarch64-v{easytier_version}.zip",
            "arm": f"https://github.com/EasyTier/EasyTier/releases/download/v{easytier_version}/easytier-linux-arm-v{easytier_version}.zip",
            "armhf": f"https://github.com/EasyTier/EasyTier/releases/download/v{easytier_version}/easytier-linux-armhf-v{easytier_version}.zip",
            "armv7": f"https://github.com/EasyTier/EasyTier/releases/download/v{easytier_version}/easytier-linux-armv7-v{easytier_version}.zip",
            "armv7hf": f"https://github.com/EasyTier/EasyTier/releases/download/v{easytier_version}/easytier-linux-armv7hf-v{easytier_version}.zip",
            "mips": f"https://github.com/EasyTier/EasyTier/releases/download/v{easytier_version}/easytier-linux-mips-v{easytier_version}.zip",
            "mipsel": f"https://github.com/EasyTier/EasyTier/releases/download/v{easytier_version}/easytier-linux-mipsel-v{easytier_version}.zip"
        },
        "MacOS": {
            "x86_64": f"https://github.com/EasyTier/EasyTier/releases/download/v{easytier_version}/easytier-macos-x86_64-v{easytier_version}.zip",
            "aarch64": f"https://github.com/EasyTier/EasyTier/releases/download/v{easytier_version}/easytier-macos-aarch64-v{easytier_version}.zip"
        },
        "FreeBSD": {
            "x86_64": f"https://github.com/EasyTier/EasyTier/releases/download/v{easytier_version}/easytier-freebsd-13.2-x86_64-v{easytier_version}.zip"
        }
    }
    return version_list


def get_easytier_version(get_github: bool =False, github_proxy: str ="") -> str:
    r"""
    获取EasyTier版本号
    :param get_github: 是否从从GitHub获取, 默认从EasyTier节点状态中获取版本号
    :param github_proxy: 能镜像api.github.com的镜像源
    :return: EasyTier版本号
    """
    if not get_github:
        get_nodes = get_easytier_nodes()
        for get_node in get_nodes:
            if "官方" in get_node.get("tags"):
                return get_node.get("version")
        return get_nodes[0].get("version")
    else:
        github_proxy += "/" if github_proxy != "" and (not github_proxy.endswith("/")) else ""
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=InsecureRequestWarning)
                return requests.get(f"{github_proxy}https://api.github.com/repos/EasyTier/EasyTier/releases/latest", verify=False).json().get("tag_name").replace("v", "", 1).replace("V", "", 1)
        except Exception:
            return get_easytier_version()


def get_easytier_nodes(number: int =100) -> list:
    r"""
    获取EasyTier节点信息
    :param number: 获取EasyTier节点的最大数量
    :return: EasyTier节点列表
    """
    return requests.get(f"https://uptime.easytier.cn/api/nodes?page=1&per_page={number}").json().get("data").get("items")


def get_easytier_nodes_address(number: int =100) -> dict:
    r"""
    获取EasyTier节点地址
    :param number: 获取EasyTier节点的最大数量
    :return: EasyTier节点地址{"Official": official_nodes_address, "Other": nodes_address}
    """
    official_nodes = []
    nodes_address = []
    get_nodes = get_easytier_nodes(number)
    for get_node in get_nodes:
        if "官方" in get_node.get("tags"):
            official_nodes.append(get_node.get("address"))
            continue
        nodes_address.append(get_node.get("address"))
    return {"Official": official_nodes, "Other": nodes_address}

