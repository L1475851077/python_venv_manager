import gradio as gr
import subprocess
import os
import sys
import json
import re
import time
import ctypes
from pathlib import Path

# ==========================================
# 0. 基础配置与持久化缓存路径
# ==========================================
def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVERYTHING_DIR = os.path.join(BASE_DIR, "everything")
EVERYTHING_EXE = os.path.join(EVERYTHING_DIR, "Everything.exe")
ES_EXE = os.path.join(EVERYTHING_DIR, "es.exe")

CACHE_FILE = os.path.join(BASE_DIR, "venv_cache.json")
# 🌟 新增：Everything 的核心索引数据库路径
DB_FILE = os.path.join(EVERYTHING_DIR, "Everything.db")

custom_css = """
/* 🌟 核心修复：强制全局使用微软雅黑/苹方等标准中文字体，防止乱码 */
* {
    font-family: "Microsoft YaHei", "PingFang SC", "Helvetica Neue", Helvetica, Arial, sans-serif !important;
}
#scroll-container { height: 450px; overflow-y: auto !important; border: 2px solid #3b82f6; padding: 15px; border-radius: 10px; background-color: #ffffff; }
.gr-checkbox-group { display: flex !important; flex-direction: column !important; }
input[type='checkbox'] { transform: scale(1.3); cursor: pointer; margin-right: 12px !important; }
.gr-checkbox-group label { display: flex !important; align-items: center; padding: 8px 15px !important; margin-bottom: 4px !important; border-radius: 8px; transition: all 0.2s ease; border: 1px solid #f0f0f0; cursor: pointer; }
.gr-checkbox-group label:hover { background-color: #eff6ff !important; border-color: #3b82f6 !important; }
#progress-area { padding: 5px; color: #3b82f6; font-weight: bold; min-height: 24px; }
"""

# ==========================================
# 1. 引擎与逻辑控制
# ==========================================
def test_engine_health():
    try:
        result = subprocess.run([ES_EXE, 'cmd.exe'], capture_output=True, text=True, errors='ignore', timeout=2)
        return len(result.stdout.strip()) > 0
    except: return False

def ensure_everything_running(force_reindex=False):
    if not os.path.exists(EVERYTHING_EXE): return False, "缺少 Everything.exe"
    try:
        res = subprocess.run('tasklist /FI "IMAGENAME eq Everything.exe"', capture_output=True, text=True, errors='ignore')
        is_running = "Everything.exe" in (res.stdout or "")
        if not is_running or force_reindex:
            if is_running: subprocess.run('taskkill /F /IM Everything.exe', capture_output=True, shell=True)
            subprocess.Popen([EVERYTHING_EXE, "-startup", "-admin", "-reindex" if force_reindex else ""])
            for _ in range(15):
                time.sleep(1)
                if test_engine_health(): return True, "就绪"
        return True, "运行中"
    except: return False, "异常"

def get_package_size(venv_path, dist_name):
    site_packages = Path(venv_path) / "Lib" / "site-packages"
    total_size = 0
    try:
        norm_name = dist_name.replace('-', '_').lower()
        infos = list(site_packages.glob(f"{norm_name}-*.dist-info")) + list(site_packages.glob(f"{norm_name}-*.egg-info"))
        if not infos: return 0
        record_file = infos[0] / "RECORD"
        if record_file.exists():
            with open(record_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    try:
                        abs_path = site_packages / line.split(',')[0].strip('"')
                        if abs_path.is_file(): total_size += abs_path.stat().st_size
                    except: continue
        return total_size / (1024 * 1024)
    except: return 0

# ==========================================
# 2. 核心异步与缓存逻辑
# ==========================================
def init_load():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
            choices = data.get("choices", [])
            selected = data.get("selected", None)
            if choices:
                return gr.update(choices=choices, value=selected), "✅ 已从本地缓存恢复状态"
        except: pass
    return gr.update(choices=[], value=None), "🟢 系统已就绪，初次使用请点击扫描..."

def step1_load_names(selected_env):
    if not selected_env: return [], gr.update(choices=[], value=[]), "请选择环境", "等待操作..."
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
            data['selected'] = selected_env
            with open(CACHE_FILE, 'w', encoding='utf-8') as f: json.dump(data, f)
    except: pass

    match = re.search(r'\[(.*?)\]$', selected_env)
    if not match: return [], gr.update(choices=[], value=[]), "❌ 路径解析失败", "错误"
    venv_path = match.group(1)
    pip_exe = os.path.join(venv_path, "Scripts", "pip.exe")
    try:
        res = subprocess.run([pip_exe, 'list', '--format=json'], capture_output=True, text=True, errors='ignore', timeout=5)
        packages = json.loads(res.stdout)
        choices = [f"{pkg['name']} ({pkg['version']})" for pkg in packages]
        return choices, gr.update(choices=choices, value=[]), "✅ 基础列表就绪", "⏳ 准备计算体积..."
    except: return [], gr.update(choices=[], value=[]), "❌ 加载失败", "错误"

def step2_enrich_sizes(selected_env, fast_choices):
    if not selected_env or not fast_choices: 
        yield fast_choices, gr.update(), "✅ 准备就绪"
        return
    match = re.search(r'\[(.*?)\]$', selected_env)
    venv_path = match.group(1)
    enriched_choices = []
    total = len(fast_choices)
    for i, item in enumerate(fast_choices):
        pkg_name = item.split(' ')[0]
        yield fast_choices, gr.update(), f"⏳ 正在计算体积 ({i+1}/{total}) : {pkg_name}"
        size_mb = get_package_size(venv_path, pkg_name)
        size_str = f"{size_mb:.1f} MB" if size_mb >= 0.1 else "<0.1 MB"
        enriched_choices.append(f"{item} ——— [{size_str}]")
    yield enriched_choices, gr.update(choices=enriched_choices), "✅ 体积计算完成"

# ==========================================
# 3. 业务动作逻辑 (含终极重置)
# ==========================================
# def scan_environments(current_env, progress=gr.Progress()):
#     progress(0, desc="正在后台唤醒 Everything 引擎...")
#     is_ready, msg = ensure_everything_running(force_reindex=False)
#     if not is_ready: return gr.update(choices=[]), f"❌ 引擎启动失败: {msg}"

#     progress(0.5, desc="正在全盘检索虚拟环境...")
#     try:
#         result = subprocess.run([ES_EXE, 'pyvenv.cfg'], capture_output=True, text=True, errors='ignore')
#         paths = (result.stdout or "").strip().split('\n')
#         venv_roots = [os.path.dirname(p) for p in paths if p.strip() and "Scripts" not in p]
#         choices = [f"📦 {os.path.basename(os.path.dirname(r))}  [{r}]" for r in venv_roots]
#         default_val = current_env if current_env in choices else (choices[0] if choices else None)
#         try:
#             with open(CACHE_FILE, 'w', encoding='utf-8') as f:
#                 json.dump({"choices": choices, "selected": default_val}, f)
#         except: pass
#         return gr.update(choices=choices, value=default_val), f"✅ 扫描完成，发现 {len(choices)} 个环境"
#     except: return gr.update(choices=[]), "扫描失败"
def scan_environments(current_env, progress=gr.Progress()):
    progress(0, desc="正在后台唤醒 Everything 引擎...")
    is_ready, msg = ensure_everything_running(force_reindex=False)
    if not is_ready: return gr.update(choices=[]), f"❌ 引擎启动失败: {msg}"

    progress(0.5, desc="正在全盘检索虚拟环境...")
    try:
        # 🌟 关键修复 1：去掉 text=True，以原生二进制(bytes)方式捕获输出
        result = subprocess.run([ES_EXE, 'pyvenv.cfg'], capture_output=True)
        
        # 🌟 关键修复 2：智能解码。先尝试 UTF-8，失败则回退到 Windows 本地编码 (mbcs/GBK)
        try:
            raw_output = result.stdout.decode('utf-8')
        except UnicodeDecodeError:
            raw_output = result.stdout.decode('mbcs', errors='ignore')
            
        paths = raw_output.strip().split('\n')
        
        # 生成环境列表
        venv_roots = [os.path.dirname(p) for p in paths if p.strip() and "Scripts" not in p]
        choices = [f"📦 {os.path.basename(os.path.dirname(r))}  [{r}]" for r in venv_roots]
        
        default_val = current_env if current_env in choices else (choices[0] if choices else None)
        
        # 写入缓存
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump({"choices": choices, "selected": default_val}, f)
        except: pass
        
        return gr.update(choices=choices, value=default_val), f"✅ 扫描完成，发现 {len(choices)} 个环境"
    except Exception as e: 
        return gr.update(choices=[]), f"扫描失败: {str(e)}"

def reset_system():
    """🌟 终极重置：杀进程、删 JSON 缓存、删 Everything 数据库索引"""
    # 1. 强杀进程释放文件锁
    subprocess.run('taskkill /F /IM Everything.exe', capture_output=True, shell=True)
    time.sleep(0.5) # 给系统半秒钟释放文件句柄
    
    # 2. 删网页缓存
    if os.path.exists(CACHE_FILE):
        try: os.remove(CACHE_FILE)
        except: pass
        
    # 3. 删 Everything 扫描数据库 (真正的恢复出厂设置)
    if os.path.exists(DB_FILE):
        try: os.remove(DB_FILE)
        except Exception as e: print(f"无法删除数据库: {e}")
    
    return (
        gr.update(choices=[], value=None), 
        gr.update(choices=[], value=[]),   
        "♻️ 已恢复出厂设置：JSON缓存与底层扫描数据库已全部粉碎。", 
        "等待操作...",                       
        []                                 
    )

def execute_pip_action(selected_env, action, package_input, selected_packages):
    match = re.search(r'\[(.*?)\]$', selected_env)
    venv_path = match.group(1)
    python_exe = os.path.join(venv_path, "Scripts", "python.exe")
    pip_exe = os.path.join(venv_path, "Scripts", "pip.exe")
    targets = [package_input.strip()] if action == "安装" else [p.split(' ')[0] for p in selected_packages]
    log = ""
    for pkg in targets:
        cmd = [python_exe, "-m", "pip", "uninstall", "-y", "pip"] if (action == "卸载" and pkg.lower() == "pip") else \
              ([pip_exe, "install", pkg] if action == "安装" else [pip_exe, "uninstall", "-y", pkg])
        log += f"--- 执行 {action}: {pkg} ---\n"
        yield log
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors='ignore')
        for line in p.stdout:
            log += line
            yield log
        p.wait()
    yield log + "\n操作完成。"

# ==========================================
# 4. 界面层
# ==========================================
with gr.Blocks(title="Python 环境管家 Pro") as demo:
    current_pkg_list = gr.State([]) 
    
    gr.Markdown("# 🗂️ Python 虚拟环境管家 (by-L小炫)")
    
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Row():
                scan_btn = gr.Button("🔍 扫描环境", variant="primary")
                reset_btn = gr.Button("♻️ 恢复首次启动状态", variant="secondary")
            
            env_dropdown = gr.Dropdown(label="当前选中的环境", choices=[], interactive=True)
            status_text = gr.Textbox(label="扫描状态状态", interactive=False)
            
            gr.Markdown("---")
            gr.Markdown("### ➕ 安装依赖")
            pkg_input = gr.Textbox(label="包名", placeholder="requests")
            install_btn = gr.Button("🚀 立即安装", variant="primary")
            terminal_log = gr.Textbox(label="终端日志", lines=12, interactive=False)
            
        with gr.Column(scale=2):
            gr.Markdown("### 📦 依赖管理列表")
            gr.Markdown(
        "[![GitHub](https://img.shields.io/badge/GitHub-访问开源仓库-181717?logo=github&style=flat-square)]"
        "(https://github.com/L1475851077/python_venv_manager) "
        " * 如果这个工具帮到了你，欢迎去 GitHub 点个 Star ⭐支持一下！*"
    )
            with gr.Row():
                refresh_btn = gr.Button("🔄 刷新列表", scale=1)
                select_all_cb = gr.Checkbox(label="全选", value=False, scale=1)
            
            progress_display = gr.Textbox(label="体积计算进度", value="等待操作...", interactive=False)
            
            with gr.Column(elem_id="scroll-container"):
                package_selector = gr.CheckboxGroup(label="已安装包清单", choices=[])
            
            uninstall_btn = gr.Button("🗑️ 批量卸载选中", variant="stop")

    # --- 核心交互 ---
    demo.load(fn=init_load, inputs=[], outputs=[env_dropdown, status_text])
    scan_btn.click(fn=scan_environments, inputs=[env_dropdown], outputs=[env_dropdown, status_text])
    
    reset_btn.click(
        fn=reset_system, 
        inputs=[], 
        outputs=[env_dropdown, package_selector, status_text, progress_display, current_pkg_list]
    )

    def handle_env_change(env): return step1_load_names(env)

    env_dropdown.change(
        fn=handle_env_change, inputs=env_dropdown, outputs=[current_pkg_list, package_selector, status_text, progress_display]
    ).then(fn=step2_enrich_sizes, inputs=[env_dropdown, current_pkg_list], outputs=[current_pkg_list, package_selector, progress_display])

    refresh_btn.click(
        fn=handle_env_change, inputs=env_dropdown, outputs=[current_pkg_list, package_selector, status_text, progress_display]
    ).then(fn=step2_enrich_sizes, inputs=[env_dropdown, current_pkg_list], outputs=[current_pkg_list, package_selector, progress_display])

    select_all_cb.change(fn=lambda s, l: gr.update(value=l if s else []), inputs=[select_all_cb, current_pkg_list], outputs=package_selector)
    install_btn.click(fn=execute_pip_action, inputs=[env_dropdown, gr.State("安装"), pkg_input, gr.State([])], outputs=[terminal_log])
    uninstall_btn.click(fn=execute_pip_action, inputs=[env_dropdown, gr.State("卸载"), gr.State(""), package_selector], outputs=[terminal_log]).then(
        fn=handle_env_change, inputs=env_dropdown, outputs=[current_pkg_list, package_selector, status_text, progress_display]
    ).then(fn=step2_enrich_sizes, inputs=[env_dropdown, current_pkg_list], outputs=[current_pkg_list, package_selector, progress_display])

if __name__ == "__main__":
    if is_admin():
        # 🌟 新增：inbrowser=True 让它启动后自动弹开默认浏览器
        demo.launch(server_name="127.0.0.1", server_port=8888, theme=gr.themes.Soft(), css=custom_css, inbrowser=True)
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{os.path.abspath(__file__)}"', None, 1)