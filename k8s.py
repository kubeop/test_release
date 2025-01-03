import yaml
import os
import docker
from docker.errors import APIError, NotFound

# 读取 all.yml 文件 
with open('group_vars/all.yml', 'r', encoding='utf-8') as file:
    data = yaml.load(file, Loader=yaml.FullLoader)

# 阿里云 ACR 镜像仓库信息
acr_repo = 'registry.cn-hangzhou.aliyuncs.com'
acr_namespace = 'kubeop'
acr_username = os.environ.get('ACR_USERNAME')
acr_password = os.environ.get('ACR_PASSWORD')

images = {
    "quay.io/cilium/cilium": data['cilium']['version'],
    "docker.io/flannel/flannel": data['flannel']['version'],
    "docker.io/flannel/flannel-cni-plugin": data['flannel']['plugin_version'],
    "docker.io/calico/kube-controllers": data['calico']['version'],
    "docker.io/calico/node": data['calico']['version'],
    "docker.io/calico/cni": data['calico']['version'],
    "docker.io/cloudnativelabs/kube-router": data['kuberouter']['version'],
    "docker.io/coredns/coredns": data['coredns']['version'],
    "registry.k8s.io/dns/k8s-dns-node-cache": data['nodelocaldns']['version'],
    "registry.k8s.io/metrics-server/metrics-server": data['metrics_server']['version'],
    "registry.k8s.io/node-problem-detector/node-problem-detector": data['npd']['version'],
    "nvcr.io/nvidia/k8s-device-plugin": data['nvidia_device_plugin']['version']
}

def login_to_registry(registry_url, username, password):
    client = docker.from_env()
    try:
        client.login(registry=registry_url, username=username, password=password)
        print(f"Login success: {registry_url}")
    except APIError as e:
        print(f"Login failed: {e}")
        return None
    return client

def pull_image(client, image_name):
    try:
        client.images.pull(f"{image_name}")
        print(f"Pull success: {image_name}")
    except NotFound:
        print(f"Tag Not Found: {image_name}")
    except APIError as e:
        print(f"Pull failed: {e}")

def tag_image(client, src_image, dst_image):
    try:
        image = client.images.get(src_image)
        image.tag(dst_image)
        print(f"Tag success: {dst_image}")
    except APIError as e:
        print(f"Tag failed: {e}")

def push_image(client, image_name):
    try:
        client.images.push(image_name)
        print(f"Push success: {image_name}")
    except APIError as e:
        print(f"Push failed: {e}")

def sync_images_to_acr():
    client = login_to_registry(acr_repo, acr_username, acr_password)
    if client:
        for image, version in images.items():
            src_repo_url = f"{image}:{version}"
            dst_repo_url = f"{acr_repo}/{acr_namespace}/{image.split('/')[-1]}:{version}"
            print(f"Syncing {src_repo_url} to {dst_repo_url}")
            pull_image(client, src_repo_url)
            tag_image(client, src_repo_url, dst_repo_url)
            push_image(client, dst_repo_url)

sync_images_to_acr()