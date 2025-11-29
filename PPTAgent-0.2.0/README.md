

# 复现这个项目的实施步骤

## 1. 首先git clone 项目并且配置好其他的组件比如mineru 
参考这个博客：

## 2. uv 创建虚拟环境
```
conda deactivate
pip install uv
uv venv # 进入目录之后
which python # 保证环境没有被污染
which pip
```

这里我使用python版本是3.12+

## 3、安装作者魔改的python-pptx
作者自己写了一个pptx库 [force-python-pptx](https://github.com/Force1ess/python-pptx)

下载源码之后，可以这样下载：
```
uv run pip install ./python-pptx-master
```

从github链接下载可以是：
```
uv pip install "git+https://ghproxy.com/https://github.com/Force1ess/python-pptx.git@main#egg=python-pptx"
```

## 4、安装相关的依赖。
```
uv run pip install -e .
```

## 5、其他的依赖，

### 5.0 image2html的库需要一个chromium-browser
```
sudo apt update && sudo apt install -y chromium-browser
```

### 5.1 fasttext
```
sudo apt install python3.12-dev
sudo apt install build-essential libopenblas-dev libblas-dev libatlas-base-dev # fasttext编译需要的依赖
uv add fasttext
```

### 5.2 torch相关
```
uv add torch
uv add transformers
uv add accelerate>=0.26.0
uv add torchvision
```

# Demo启动步骤

具体的启动步骤是：
- export HF_ENDPOINT=https://hf-mirror.com （启动huggingface镜像）
- huggingface-cli login (登陆账号，保证链接，需要access key)
- 启动manerU （请看manerU文件夹readme.md）
- source .venv/bin/activate
- source load_api.sh (使用的是qwen最新的多模态模型，自己注册填写)
- python backend.py (启动后端)
- npm install
- npm run serve （启动前端）





# Issues
下面所有的代码是在2025年11月之前发现，使用作者release 0.2.0的代码包
## 1、parse_pdf 这个异步协程函数 返回值是一个谜
我添加了await获取返回值，然后这个函数里面也没有返回，但是后面处理逻辑是需要（存疑，只是代码里面写了）这个函数的返回值，因为我在运行的时候报错nonetype error了
最终我加了await，并且返回了content也就是asyncllm对pdf的解析，在两个pdf生成pptx上面都成功了。顺便说一下，作者这个函数似乎是把提取的结果放到某一个路径下面，这个是有用的，但返回值是一个谜。


