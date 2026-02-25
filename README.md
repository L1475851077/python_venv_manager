
# 🗂️ Python Venv Web Manager Pro (虚拟环境管家)

![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Gradio](https://img.shields.io/badge/Gradio-6.0-orange)

 Windows系统的Python 虚拟环境批量管理工具
一个基于 Web UI 的轻量级、超高速 Python 虚拟环境批量管理工具，清晰了解你在各各项目中python -m创建的项目虚拟环境，以及管理虚拟环境中安装的依赖，无需激活虚拟环境，即可让你了解各个虚拟环境的依赖状态。
深度整合了 [voidtools Everything](https://www.voidtools.com/) 引擎，让你彻底告别在终端里四处寻找 `activate` 脚本的痛苦，实现 **毫秒级全盘扫描** 和 **依赖包磁盘体积可视化**。

---

## ✨ 核心特性

- 🚀 **毫秒级全盘检索**：底层挂载 Everything 引擎，瞬间找出硬盘每个角落的 `.venv` 环境。
- 📦 **异步依赖管理**：极速拉取环境内已安装的 Python 包，并在后台异步计算每个包的**真实磁盘占用（MB）**，拯救 C 盘空间。
- ♻️ **智能持久化缓存**：刷新网页不丢状态，按需唤醒底层扫描引擎，平日完全“零占用”挂机。支持一键“恢复首次启动状态”。
- 🛡️ **全自动管理员提权**：配套原生 `.bat` 启动器，双击自动申请 UAC 权限并弹开浏览器，小白也能一秒上手。
- 🎨 **现代 Web UI**：基于最新的 Gradio 6.0 框架，独立渲染进度条与异步列表，交互如德芙般丝滑。

## 📸 界面预览

![](https://github.com/L1475851077/python_venv_manager/blob/main/images/start.png?raw=true)
![](https://github.com/L1475851077/python_venv_manager/blob/main/images/starting.png?raw=true)


## 🚀 快速开始

### 1. 准备工作
请确保你的电脑上安装了 Python 3.8 或以上版本，并安装必要的依赖：
```bash
pip install gradio
```

双击`Start_venv_Manager.bat`或执行` python .\venv_web_manager.py`命令启动。注意需要管理员权限，弹窗时请允许。



## 📄 开源协议 (License)

本项目的原创源代码部分采用 **[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)** 协议进行许可。

**这意味着：**
1. ✅ **允许商用**：你可以自由地将本代码用于商业项目、闭源衍生产品中。
2. ✅ **允许修改与分发**：你可以随意修改代码并重新发布。
3. ❗ **必须保留声明**：在分发时，必须包含原始的 Apache-2.0 许可证副本，并保留原作者的版权声明。如果在源文件中做了修改，必须在被修改的文件中进行说明。
4. 🚫 **免责声明**：作者不对由于使用本软件造成的任何直接或间接损失负责，软件按“原样”提供。

**⚠️ 第三方依赖特别声明：**
本项目所捆绑的 `Everything.exe` 和 `es.exe` 属于 [voidtools](https://www.voidtools.com/) 的免费软件（Freeware），受其官方最终用户许可协议（EULA）约束，**不属于**本项目的 Apache-2.0 开源授权范围。
