# AUTO_TKINTER_FIX - PyInstaller tkinter 路径修复（打包工具自动注入）
import sys, os
if getattr(sys, 'frozen', False):
    _tk_base = sys._MEIPASS
    for _env_var, _subdir in [('TCL_LIBRARY', 'tcl'), ('TK_LIBRARY', 'tk')]:
        _path = os.path.join(_tk_base, _subdir)
        if os.path.exists(_path):
            os.environ[_env_var] = _path
    _dlls = os.path.join(_tk_base, 'DLLs')
    if os.path.exists(_dlls):
        os.environ['PATH'] = _dlls + os.pathsep + os.environ.get('PATH', '')
# END_AUTO_TKINTER

# AUTO_INJECTED_WORKDIR - 设置为exe所在目录
import os
import sys
import ctypes
import tempfile

class ExePathManager:
    @staticmethod
    def is_frozen() -> bool:
        frozen_flags = [
            getattr(sys, 'frozen', False),
            hasattr(sys, '_MEI_ARCHIVE'),
            getattr(sys, 'nuitka_is_frozen', False),
        ]
        if not any(frozen_flags):
            if sys.argv[0].lower().endswith('.exe'):
                return True
            if 'temp' in sys.executable.lower() or 'onefile' in sys.executable.lower():
                return True
            if sys.platform == 'win32':
                try:
                    buffer = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
                    ctypes.windll.kernel32.GetModuleFileNameW(
                        ctypes.wintypes.HMODULE(0),
                        buffer,
                        ctypes.wintypes.MAX_PATH
                    )
                    exe_path = buffer.value
                    if exe_path.lower().endswith('.exe'):
                        return True
                except:
                    pass
        return any(frozen_flags)

    @staticmethod
    def get_real_exe_path() -> str:
        if not ExePathManager.is_frozen():
            return os.path.abspath(__file__)
        if sys.platform == 'win32':
            try:
                buffer = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
                ctypes.windll.kernel32.GetModuleFileNameW(
                    ctypes.wintypes.HMODULE(0),
                    buffer,
                    ctypes.wintypes.MAX_PATH
                )
                real_path = buffer.value
                if os.path.exists(real_path) and os.path.isfile(real_path):
                    return real_path
            except:
                pass
        if hasattr(sys, '_MEIPASS'):
            return sys.executable
        return os.path.abspath(sys.argv[0])

    @staticmethod
    def get_exe_directory() -> str:
        return os.path.dirname(ExePathManager.get_real_exe_path())

    @staticmethod
    def is_temp_directory(path: str) -> bool:
        temp_dirs = [
            tempfile.gettempdir(),
            os.path.join(os.environ.get('TEMP', ''), ''),
            os.path.join(os.environ.get('TMP', ''), ''),
        ]
        abs_path = os.path.abspath(path)
        return any(abs_path.startswith(temp_dir) for temp_dir in temp_dirs if temp_dir)

if ExePathManager.is_frozen():
    exe_dir = ExePathManager.get_exe_directory()
    if os.path.exists(exe_dir):
        os.chdir(exe_dir)
# END AUTO_INJECTED_WORKDIR
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk, messagebox
import threading
import sys
import os
import re
import pyinstxtractorcn
from datetime import datetime
import time
import subprocess
import shutil
import importlib.util
import requests
import json
import base64
from io import BytesIO

class PyInstxtractorCN_GUI:
    def __init__(self, root):
        self.root = root
        
        # 获取屏幕尺寸，设置为屏幕的70%
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width * 0.7)
        window_height = int(screen_height * 0.75)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.title("pyinstxtractorcnGUI 1.3.1")
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(int(window_width * 0.8), int(window_height * 0.8))
        self.root.configure(bg="#f0f0f0")
        
        # 设置窗口图标
        self._set_window_icon()
        
        # 保存原始stdout以便恢复
        self.original_stdout = sys.stdout
        
        self.file_path = ""
        self.output_dir = ""
        self.extraction_active = False
        self.decompile_tool = "pylingual"
        self.available_tools = {}
        self.has_pyc_decompiler = False
        self.pyc_decompiler_module = None
        self.pyc_decompiler_path = None
        self.local_magic_map = None
        self.remote_magic_map = None
        self.current_preview_file = None
        
        # 左侧面板宽度
        self.left_panel_width = int(window_width * 0.25)
        self.is_resizing = False
        
        # 默认更新配置
        self.default_update_url = "https://raw.githubusercontent.com/rajveerexe/PycDecompiler/main/PycDecompiler.py"
        self.custom_update_url = ""
        self.update_config = {
            "github_repo": "rajveerexe/PycDecompiler",
            "file_name": "PycDecompiler.py",
            "backup_suffix": ".bak",
            "default_url": self.default_update_url
        }
        
        # 尝试导入外部的PycDecompiler.py
        self._import_pyc_decompiler()
        
        # 加载保存的自定义网址
        self._load_custom_url()
        
        # 反编译工具配置（包含反混淆工具）
        self.decompile_tools = {
            "pylingual": {
                "name": "PyLingual", 
                "cmd": "online", 
                "description": "【推荐】在线反编译服务，支持混淆字节码，效果最好",
                "check_method": "online",
                "type": "online",
                "quality": "⭐⭐⭐⭐⭐"
            },
            "pyc_decompiler": {
                "name": "PycDecompiler", 
                "cmd": "local",
                "description": "本地脚本，通过PyLingual在线服务反编译（需要网络）",
                "check_method": "local",
                "type": "local",
                "quality": "⭐⭐⭐⭐"
            },
            "pycdc": {
                "name": "pycdc", 
                "cmd": "pycdc", 
                "description": "C++编写，速度快，但混淆代码可能失败",
                "check_method": "exe",
                "type": "local",
                "quality": "⭐⭐⭐"
            },
            "py_cdec": {
                "name": "py-cdec", 
                "cmd": "py-cdec", 
                "description": "pip install py-cdec，C++实现的反编译工具",
                "check_method": "both",
                "module": "cdec",
                "type": "local",
                "quality": "⭐⭐⭐"
            },
            "de4py": {
                "name": "De4py", 
                "cmd": "de4py",
                "description": "【反混淆】专门处理混淆的Python代码，支持PyArmor等",
                "check_method": "pip",
                "module": "de4py",
                "type": "deobfuscator",
                "quality": "⭐⭐⭐⭐"
            },
            "pychd": {
                "name": "PyChD",
                "cmd": "pychd",
                "description": "【LLM辅助】混合规则+GPT反编译，支持Python 3.0-3.14\n安装: pip install pychd",
                "check_method": "pip",
                "module": "pychd",
                "type": "decompiler",
                "quality": "⭐⭐⭐⭐"
            },
            "pydumpck": {
                "name": "PyDumpck", 
                "cmd": "pydumpck",
                "description": "【反混淆】多线程解包工具，支持加密exe/pyc",
                "check_method": "pip",
                "module": "pydumpck",
                "type": "deobfuscator",
                "quality": "⭐⭐⭐"
            },
            "pyobfus": {
                "name": "PyObfus",
                "cmd": "pyobfus",
                "description": "【反混淆】AST转换，支持反混淆PyArmor等混淆代码\n安装: pip install pyobfus",
                "check_method": "pip",
                "module": "pyobfus",
                "type": "deobfuscator",
                "quality": "⭐⭐⭐⭐"
            },
            "uncompyle6": {
                "name": "uncompyle6", 
                "cmd": "uncompyle6", 
                "description": "Python编写，混淆代码基本无法处理",
                "check_method": "both",
                "module": "uncompyle6",
                "type": "local",
                "quality": "⭐⭐"
            },
            "decompyle3": {
                "name": "decompyle3", 
                "cmd": "decompyle3", 
                "description": "针对Python 3，混淆代码效果差",
                "check_method": "both",
                "module": "decompyle3",
                "type": "local",
                "quality": "⭐⭐"
            }
        }
        
        # 初始化状态变量
        self.status_var = tk.StringVar(value="就绪")
        self.auto_retry_var = tk.BooleanVar(value=True)  # 默认开启自动轮询
        self._create_widgets()
        
        # 设置拖拽功能
        self._setup_drag_drop()
        
        # 自动查找可用的反编译工具
        self._find_available_tools()

        # 显示本地版本信息
        if self.has_pyc_decompiler and self.local_magic_map:
            versions = ', '.join(self.local_magic_map.keys())
            self._log(f"📦 本地 PycDecompiler 支持版本: {versions}", "success")
        
        sys.stdout = self
    
    def __del__(self):
        if hasattr(self, 'original_stdout'):
            sys.stdout = self.original_stdout
    
    def _set_window_icon(self):
        """设置窗口图标"""
        try:
            # 尝试加载外部的icon.ico文件
            icon_paths = [
                os.path.join(os.path.dirname(sys.argv[0]), "icon.ico"),
                os.path.join(os.getcwd(), "icon.ico"),
                os.path.join(os.path.dirname(__file__), "icon.ico")
            ]
            
            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
                    self._log(f"✓ 已加载图标: {icon_path}", "success")
                    return True
        except Exception as e:
            pass
    
    def _load_custom_url(self):
        """加载保存的自定义网址"""
        config_file = os.path.join(os.path.dirname(sys.argv[0]), "pyc_decompiler_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.custom_update_url = config.get("custom_url", "")
                    if self.custom_update_url:
                        self._log(f"已加载自定义更新网址: {self.custom_update_url}", "info")
            except Exception as e:
                self._log(f"加载配置文件失败: {str(e)}", "warning")
    
    def _save_custom_url(self):
        """保存自定义网址"""
        config_file = os.path.join(os.path.dirname(sys.argv[0]), "pyc_decompiler_config.json")
        try:
            config = {"custom_url": self.custom_update_url}
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self._log(f"保存配置文件失败: {str(e)}", "warning")
            return False
    
    def _import_pyc_decompiler(self):
        """导入外部的PycDecompiler.py文件并提取magic_map"""
        possible_paths = [
            os.path.join(os.getcwd(), "PycDecompiler.py"),
            os.path.join(os.path.dirname(sys.argv[0]), "PycDecompiler.py"),
            os.path.join(os.path.dirname(__file__), "PycDecompiler.py"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    import re
                    magic_map_pattern = r'magic_map\s*=\s*\{(.*?)\n\}'
                    match = re.search(magic_map_pattern, content, re.DOTALL)

                    if match:
                        magic_content = match.group(1)
                        versions_found = re.findall(r'"([\d.]+)"\s*:', magic_content)
                        if versions_found:
                            self.local_magic_map = {v: True for v in versions_found}

                    spec = importlib.util.spec_from_file_location("PycDecompiler", path)
                    if spec:
                        if "PycDecompiler" in sys.modules:
                            del sys.modules["PycDecompiler"]

                        self.pyc_decompiler_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(self.pyc_decompiler_module)
                        self.has_pyc_decompiler = True
                        self.pyc_decompiler_path = path

                        version = getattr(self.pyc_decompiler_module, '__version__', '未知版本')
                        author = getattr(self.pyc_decompiler_module, '__author__', '未知作者')

                        self._log(f"✓ 加载 PycDecompiler.py 成功", "success")
                        self._log(f"  路径: {path}", "info")
                        self._log(f"  版本: {version}", "info")
                        self._log(f"  作者: {author}", "info")

                        return True

                except Exception as e:
                    self._log(f"加载 PycDecompiler.py 失败: {str(e)}", "warning")

        self.has_pyc_decompiler = False
        return False
    
    def _preview_code(self, py_file_path):
        """预览反编译后的代码"""
        if not py_file_path or not os.path.exists(py_file_path):
            return
        
        try:
            with open(py_file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            if len(code) > 50000:
                code = code[:50000] + "\n\n... (代码过长，已截断，请使用导出功能查看完整文件)"
            
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, code)
            
            self.preview_text.config(state=tk.DISABLED)
            self.current_preview_file = py_file_path
            
            self._log(f"✓ 代码预览已加载: {os.path.basename(py_file_path)} ({len(code)} 字符)", "success")
        except Exception as e:
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, f"预览失败: {str(e)}")
            self.preview_text.config(state=tk.DISABLED)
            self._log(f"预览失败: {str(e)}", "warning")
    
    def _export_preview_code(self):
        """导出预览的代码到文件"""
        if not self.current_preview_file or not os.path.exists(self.current_preview_file):
            messagebox.showwarning("警告", "没有可导出的代码，请先转换一个pyc文件")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存代码文件",
            defaultextension=".py",
            filetypes=[("Python文件", "*.py"), ("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile=os.path.basename(self.current_preview_file)
        )
        
        if file_path:
            try:
                shutil.copy2(self.current_preview_file, file_path)
                self._log(f"✓ 代码已导出到: {file_path}", "success")
                messagebox.showinfo("导出成功", f"代码已保存到:\n{file_path}")
            except Exception as e:
                self._log(f"导出失败: {str(e)}", "error")
                messagebox.showerror("导出失败", f"导出代码时出错:\n{str(e)}")
    
    def _copy_preview_code(self):
        """复制预览的代码到剪贴板"""
        if not self.current_preview_file or not os.path.exists(self.current_preview_file):
            messagebox.showwarning("警告", "没有可复制的代码，请先转换一个pyc文件")
            return
        
        try:
            with open(self.current_preview_file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            self._log(f"✓ 代码已复制到剪贴板 ({len(code)} 字符)", "success")
            self.status_var.set(f"已复制 {len(code)} 字符到剪贴板")
            self.root.after(2000, lambda: self.status_var.set("就绪"))
        except Exception as e:
            self._log(f"复制失败: {str(e)}", "error")
            messagebox.showerror("复制失败", f"复制代码时出错:\n{str(e)}")
    
    def _refresh_preview(self):
        """刷新预览"""
        if self.current_preview_file and os.path.exists(self.current_preview_file):
            self._preview_code(self.current_preview_file)
            self._log(f"✓ 预览已刷新: {os.path.basename(self.current_preview_file)}", "info")
    
    def _check_for_updates(self):
        """检查PycDecompiler.py是否有新版本"""
        if not self.has_pyc_decompiler:
            return
        
        if self.local_magic_map:
            versions = ', '.join(self.local_magic_map.keys())
            self._log(f"📦 本地 PycDecompiler 支持版本: {versions}", "success")
        
        def check():
            try:
                self._log("正在联网检查更新...", "info")
                self.root.after(0, lambda: self.update_btn.config(text="联网检查中...", state=tk.DISABLED))
                
                update_sources = []
                if self.custom_update_url:
                    update_sources.append(("自定义网址", self.custom_update_url))
                update_sources.append(("默认GitHub", self.update_config["default_url"]))
                
                downloaded_content = None
                
                for source_name, source_url in update_sources:
                    try:
                        self._log(f"尝试从 {source_name} 获取...", "info")
                        headers = {"User-Agent": "Mozilla/5.0"}
                        response = requests.get(source_url, headers=headers, timeout=10)
                        
                        if response.status_code == 200:
                            downloaded_content = response.text
                            self._log(f"✓ 从 {source_name} 获取成功", "success")
                            break
                    except Exception as e:
                        self._log(f"从 {source_name} 获取失败: {str(e)}", "warning")
                
                if not downloaded_content:
                    self._log("❌ 网络连接失败，无法检查更新", "warning")
                    self.root.after(0, lambda: self.update_btn.config(text="📦 网络失败", state=tk.NORMAL, bg="#e74c3c"))
                    return
                
                import re
                magic_map_pattern = r'magic_map\s*=\s*\{([^}]+)\}'
                match = re.search(magic_map_pattern, downloaded_content, re.DOTALL)
                
                if match:
                    versions_found = re.findall(r'"([\d.]+)"\s*:', match.group(1))
                    if versions_found:
                        remote_versions = set(versions_found)
                        self._log(f"🌐 远程版本支持: {', '.join(versions_found)}", "info")
                        
                        if self.local_magic_map:
                            local_versions = set(self.local_magic_map.keys())
                            
                            if local_versions != remote_versions:
                                new_versions = remote_versions - local_versions
                                if new_versions:
                                    self._log(f"  ➕ 新增版本: {', '.join(sorted(new_versions))}", "success")
                                self.remote_magic_map = {v: True for v in versions_found}
                                self.root.after(0, lambda: self.update_btn.config(text="⬇ 发现新版本", state=tk.NORMAL, bg="#e74c3c"))
                            else:
                                self._log("✓ 已是最新版本，无需更新", "success")
                                self.root.after(0, lambda: self.update_btn.config(text="✓ 已是最新", state=tk.DISABLED, bg="#2ecc71"))
                    else:
                        self._log("无法解析远程版本信息", "warning")
                else:
                    self._log("无法解析magic_map", "warning")
                    
            except Exception as e:
                self._log(f"检查更新失败: {str(e)}", "warning")
                self.root.after(0, lambda: self.update_btn.config(text="⬇ 检查失败", state=tk.NORMAL, bg="#e74c3c"))
        
        threading.Thread(target=check, daemon=True).start()
    
    def _set_custom_url(self):
        """设置自定义更新网址"""
        dialog = tk.Toplevel(self.root)
        dialog.title("设置自定义更新网址")
        dialog.geometry("600x250")
        dialog.configure(bg="#f0f0f0")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (250 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        tk.Label(dialog, text="自定义更新网址:", bg="#f0f0f0", 
                font=("Arial", 10)).pack(pady=(20, 5))
        
        url_entry = tk.Entry(dialog, width=70, font=("Arial", 10))
        url_entry.pack(pady=5, padx=20)
        url_entry.insert(0, self.custom_update_url)
        
        tk.Label(dialog, text="提示: 留空则使用默认GitHub源\n支持的网址格式: https://raw.githubusercontent.com/用户名/仓库名/分支/文件名.py", 
                bg="#f0f0f0", font=("Arial", 8), fg="#666", justify=tk.LEFT).pack(pady=5)
        
        def save_url():
            new_url = url_entry.get().strip()
            self.custom_update_url = new_url
            self._save_custom_url()
            if new_url:
                self._log(f"已设置自定义更新网址: {new_url}", "success")
            else:
                self._log("已清除自定义更新网址，将使用默认源", "info")
            dialog.destroy()
            self._check_for_updates()
        
        btn_frame = tk.Frame(dialog, bg="#f0f0f0")
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="保存", command=save_url,
                 width=10, bg="#2ecc71", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=dialog.destroy,
                 width=10, bg="#e74c3c", fg="white").pack(side=tk.LEFT, padx=5)
    
    def _download_update(self):
        """下载更新PycDecompiler.py"""
        if not self.remote_magic_map:
            self._check_for_updates()
            messagebox.showinfo("提示", "正在检查更新，请稍后点击重试")
            return
        
        result = messagebox.askyesno(
            "确认更新", 
            f"当前支持Python版本: {', '.join(self.local_magic_map.keys()) if self.local_magic_map else '未知'}\n"
            f"最新支持Python版本: {', '.join(self.remote_magic_map.keys())}\n\n"
            f"是否下载最新版本？"
        )
        
        if not result:
            return
        
        def download():
            try:
                self._log("开始下载 PycDecompiler.py 更新...", "info")
                self.update_btn.config(text="下载中...", state=tk.DISABLED)
                
                update_sources = []
                if self.custom_update_url:
                    update_sources.append(("自定义网址", self.custom_update_url))
                update_sources.append(("默认GitHub", self.update_config["default_url"]))
                
                downloaded_content = None
                
                for source_name, source_url in update_sources:
                    try:
                        headers = {"User-Agent": "Mozilla/5.0"}
                        response = requests.get(source_url, headers=headers, timeout=30)
                        
                        if response.status_code == 200:
                            downloaded_content = response.text
                            self._log(f"从 {source_name} 下载成功", "success")
                            break
                    except Exception as e:
                        self._log(f"从 {source_name} 下载失败: {str(e)}", "warning")
                
                if not downloaded_content:
                    raise Exception("所有更新源均失败")
                
                backup_path = self.pyc_decompiler_path + ".bak"
                if os.path.exists(self.pyc_decompiler_path):
                    shutil.copy2(self.pyc_decompiler_path, backup_path)
                    self._log(f"已备份原文件: {os.path.basename(backup_path)}", "info")
                
                with open(self.pyc_decompiler_path, 'w', encoding='utf-8') as f:
                    f.write(downloaded_content)
                
                self._log(f"✓ 下载完成！", "success")
                self._log("正在重新加载模块...", "info")
                
                if self._import_pyc_decompiler():
                    self._log("✓ 模块重新加载成功", "success")
                    self.update_btn.config(text=f"✓ 已更新", state=tk.DISABLED, bg="#2ecc71")
                    messagebox.showinfo("更新成功", "PycDecompiler.py 已更新成功！")
                else:
                    self._log("模块重新加载失败，请重启程序", "warning")
                    self.update_btn.config(text="重试更新", state=tk.NORMAL, bg="#e74c3c")
                    
            except Exception as e:
                self._log(f"下载失败: {str(e)}", "error")
                self.update_btn.config(text="⬇ 更新失败", state=tk.NORMAL, bg="#e74c3c")
                messagebox.showerror("更新失败", f"下载失败: {str(e)}")
        
        threading.Thread(target=download, daemon=True).start()
    
    def _clear_log(self):
        """清空日志"""
        if messagebox.askyesno("确认清空", "确定要清空所有日志吗？"):
            self.log_area.delete(1.0, tk.END)
            self._log("日志已清空", "info")
    
    def _export_log(self):
        """导出日志"""
        log_content = self.log_area.get(1.0, tk.END)
        if not log_content.strip():
            messagebox.showwarning("警告", "日志为空，无法导出")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存日志文件",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("日志文件", "*.log"), ("所有文件", "*.*")],
            initialfile=f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                self._log(f"日志已导出到: {file_path}", "success")
                messagebox.showinfo("导出成功", f"日志已保存到:\n{file_path}")
            except Exception as e:
                self._log(f"导出日志失败: {str(e)}", "error")
                messagebox.showerror("导出失败", f"导出日志时出错:\n{str(e)}")
    
    def _update_button_visibility(self):
        """根据选择的工具更新按钮显示状态"""
        try:
            if self.decompile_tool == "pyc_decompiler" and self.has_pyc_decompiler:
                self.button_row.pack(fill="x", pady=(5, 0))
                self.update_btn.config(text="⬇ 检查更新", state=tk.NORMAL, bg="#3498db")
                self.settings_btn.config(state=tk.NORMAL, bg="#95a5a6")
            else:
                self.button_row.pack_forget()
        except Exception as e:
            pass
    
    def _setup_drag_drop(self):
        """设置拖拽功能"""
        try:
            if hasattr(self.root, 'drop_target_register'):
                self.left_frame.drop_target_register('DND_Files')
                self.left_frame.dnd_bind('<<Drop>>', self._on_file_drop)
                self.btn_container.drop_target_register('DND_Files')
                self.btn_container.dnd_bind('<<Drop>>', self._on_file_drop)
                self.preview_text.drop_target_register('DND_Files')
                self.preview_text.dnd_bind('<<Drop>>', self._on_file_drop)
                
                self.drag_hint = tk.Label(self.btn_container, 
                                          text="💡 提示：可直接拖拽EXE文件到此区域",
                                          bg="#e0e0e0", fg="#666", 
                                          font=("Arial", 8, "italic"))
                self.drag_hint.pack(pady=(0, 10))
                self.drag_supported = True
            else:
                self.drag_supported = False
        except:
            self.drag_supported = False
    
    def _on_file_drop(self, event):
        """处理文件拖拽"""
        if not self.drag_supported:
            return
        
        files = event.data
        if files.startswith('{') and files.endswith('}'):
            files = files[1:-1]
        
        if isinstance(files, str):
            if ' ' in files and not files.startswith('"'):
                file_list = self.root.tk.splitlist(files)
                if file_list:
                    files = file_list[0]
            files = files.strip('{}')
        
        if os.path.exists(files) and files.lower().endswith('.exe'):
            self.file_path = files
            self._update_info()
            self.status_var.set(f"已选择文件：{os.path.basename(files)}")
            self._log(f"通过拖拽选择文件：{files}", "success")
            self.left_frame.config(bg="#d4edda")
            self.root.after(1000, lambda: self.left_frame.config(bg="#e0e0e0"))
        else:
            self._log(f"拖拽的文件无效或不是exe文件：{files}", "warning")
            self.left_frame.config(bg="#ffdddd")
            self.root.after(1000, lambda: self.left_frame.config(bg="#e0e0e0"))
    
    def _check_pip_package(self, module_name):
        """检查Python包是否已安装"""
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is not None:
                return True
            
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', module_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _find_available_tools(self):
        """自动查找可用的反编译工具"""
        available_tools = {}
        
        # 在线工具总是可用
        available_tools["pylingual"] = "online"
        self._log(f"✓ PyLingual (在线服务) - 支持混淆字节码，效果最好", "success")
        
        if self.has_pyc_decompiler:
            available_tools["pyc_decompiler"] = "local"
            self._log(f"✓ PycDecompiler (本地脚本) - 支持marshal转换", "success")
        
        # 检查本地工具
        for tool_key, tool_info in self.decompile_tools.items():
            if tool_key in ["pylingual", "pyc_decompiler"]:
                continue
            
            tool_found = False
            tool_path = None
            
            # 检查命令是否存在
            cmd = tool_info["cmd"]
            if shutil.which(cmd):
                tool_path = shutil.which(cmd)
                tool_found = True
                self._log(f"✓ 找到 {tool_info['name']} {tool_info['quality']}", "success")
            elif tool_info.get("check_method") in ["both", "pip"]:
                module_name = tool_info.get("module", cmd)
                if self._check_pip_package(module_name):
                    tool_found = True
                    tool_path = f"python -m {module_name}"
                    self._log(f"✓ 找到 {tool_info['name']} {tool_info['quality']} (Python包)", "success")
            
            if tool_found and tool_path:
                available_tools[tool_key] = tool_path
            else:
                available_tools[tool_key] = None
        
        self.available_tools = available_tools

        if hasattr(self, 'tool_combo'):
            self._update_tool_combo()
        
        self._log("=" * 50, "info")
        self._log("【工具推荐】", "success")
        self._log("  🌐 PyLingual - 在线服务，支持混淆字节码，完全反编译（推荐）", "info")
        if self.has_pyc_decompiler:
            self._log(f"  📦 PycDecompiler - 本地脚本，通过在线服务反编译", "info")
        self._log("  🛡️De4py - 反混淆工具，专门处理PyArmor等混淆代码", "info")
        self._log("  🔓 PyDumpck - 反混淆工具，支持加密exe/pyc", "info")
        self._log("  ⚡ pycdc/py-cdec - C++实现，混淆代码可能失败", "info")
        self._log("=" * 50, "info")
    
    def _update_tool_combo(self):
        """更新工具下拉菜单"""
        self.tool_combo['values'] = []
        
        tool_list = [
            "🌐 PyLingual⭐⭐⭐⭐⭐",
            "📦 PycDecompiler ⭐⭐⭐⭐",
            "🔓 De4py ⭐⭐⭐⭐(反混淆)",
            "🔓 PyDumpck ⭐⭐⭐⭐(多线程)",
            "🤖 PyChD ⭐⭐⭐⭐(LLM辅助)",
            "🛡 PyObfus ⭐⭐⭐⭐(反混淆)",
            "⚡ pycdc ⭐⭐⭐",
            "⚡ py-cdec ⭐⭐⭐",
            "🐍 uncompyle6 ⭐⭐",
            "🐍 decompyle3 ⭐⭐"
        ]
        
        self.tool_combo['values'] = tool_list
        self.tool_combo.set(tool_list[0])
        self.decompile_tool = "pylingual"
        # 动态计算最大宽度
        max_width = 0
        for item in tool_list:
            # 估算字符宽度（中文字符约2倍宽度）
            width = sum(2 if ord(c) > 127 else 1 for c in item)
            if width > max_width:
                max_width = width
    
        # 设置下拉框宽度（字符数）
        self.tool_combo.config(width=max_width + 2)
        self.tool_combo.config(state="readonly")
        self._update_button_visibility()
    
    def _on_tool_change(self, event=None):
        """工具选择变化时的处理"""
        selected = self.tool_combo.get()
        
        if "PycDecompiler" in selected:
            self.decompile_tool = "pyc_decompiler"
        elif "PyLingual" in selected:
            self.decompile_tool = "pylingual"
        elif "De4py" in selected:
            self.decompile_tool = "de4py"
        elif "PyChD" in selected:
            self.decompile_tool = "pychd"
        elif "PyObfus" in selected:
            self.decompile_tool = "pyobfus"
        elif "PyDumpck" in selected:
            self.decompile_tool = "pydumpck"
        elif "pycdc" in selected.lower():
            self.decompile_tool = "pycdc"
        elif "py-cdec" in selected.lower():
            self.decompile_tool = "py_cdec"
        elif "uncompyle6" in selected.lower():
            self.decompile_tool = "uncompyle6"
        elif "decompyle3" in selected.lower():
            self.decompile_tool = "decompyle3"
        else:
            self.decompile_tool = "pylingual"

        self._update_button_visibility()

        tool_info = self.decompile_tools.get(self.decompile_tool, {})
        desc = tool_info.get("description", "")
        quality = tool_info.get("quality", "")
        
        # 检查工具是否可用
        is_available = self.available_tools.get(self.decompile_tool) is not None
        if not is_available and self.decompile_tool not in ["pylingual", "pyc_decompiler"]:
            self._log(f"⚠ {self.decompile_tool} 尚未安装", "warning")
            if self.decompile_tool in ["de4py", "pydumpck", "pychd", "pyobfus"]:
                self._log(f"   安装命令: pip install {self.decompile_tool}", "info")
            elif self.decompile_tool in ["uncompyle6", "decompyle3"]:
                self._log(f"   安装命令: pip install {self.decompile_tool}", "info")
            elif self.decompile_tool == "py_cdec":
                self._log(f"   安装命令: pip install py-cdec", "info")
        else:
            self._log(f"切换反编译工具为: {self.decompile_tool} {quality}", "info")
            self._log(f"  说明: {desc}", "info")

        if self.decompile_tool == "pylingual":
            self.convert_desc.config(text="(推荐使用PyLingual在线服务，支持混淆)", fg="#06d6a0")
        elif self.decompile_tool in ["de4py", "pydumpck", "pychd", "pyobfus"]:
            self.convert_desc.config(text="(反混淆工具，专门处理混淆代码)", fg="#e74c3c")
        elif self.decompile_tool == "pyc_decompiler":
            self.convert_desc.config(text="(使用PycDecompiler脚本)", fg="#9b59b6")
        else:
            self.convert_desc.config(text="(工具对混淆代码效果差)", fg="#ffd166")
    
    def _create_widgets(self):
        # 主标题
        title_label = tk.Label(self.root, text="PyinstxtractorcnGUI 1.3.1", 
                               font=("黑体", 18, "bold"),
                               bg="#f0f0f0", fg="#2c3e50")
        title_label.pack(pady=15)
        
        # 主框架
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, padx=20, pady=10, expand=True)
        
        # 左侧操作面板
        self.left_frame = tk.Frame(main_frame, bg="#e0e0e0", bd=2, relief=tk.GROOVE, width=self.left_panel_width)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=10)
        self.left_frame.pack_propagate(False)
        
        # 调整大小分隔线
        self.resize_bar = tk.Frame(main_frame, bg="#999999", cursor="sb_h_double_arrow", width=6)
        self.resize_bar.place(x=self.left_panel_width - 3, y=10, width=6, height=self.left_frame.winfo_height())
        
        self.resize_bar.bind("<ButtonPress-1>", self._start_resize)
        self.resize_bar.bind("<B1-Motion>", self._resize_left_panel)
        self.resize_bar.bind("<ButtonRelease-1>", self._stop_resize)
        self.left_frame.bind("<Configure>", self._update_resize_bar)

        self.btn_container = tk.Frame(self.left_frame, bg="#e0e0e0", padx=20, pady=20)
        self.btn_container.pack(anchor=tk.CENTER)
        
        # 操作提示
        tip_label = tk.Label(self.btn_container, text="操作步骤:", bg="#e0e0e0", anchor="w", 
                            font=("Arial", 9, "bold"))
        tip_label.pack(fill="x", pady=(0, 5))
        
        steps = [
            "1. 选择或拖拽EXE文件",
            "2. 设置输出目录(可选)",
            "3. 点击开始解包"
        ]
        for step in steps:
            step_label = tk.Label(self.btn_container, text=step, bg="#e0e0e0", anchor="w", 
                                 font=("Arial", 8))
            step_label.pack(fill="x", padx=5)
        
        # 按钮区域
        select_file_btn = tk.Button(self.btn_container, text="📁 选择文件", command=self._select_file,
                                   width=15, height=2, bg="#3498db", fg="white", 
                                   font=("Arial", 10))
        select_file_btn.pack(pady=8)
        
        select_dir_btn = tk.Button(self.btn_container, text="📂 选择输出目录", command=self._select_output_dir,
                                  width=15, height=2, bg="#2ecc71", fg="white", 
                                  font=("Arial", 10))
        select_dir_btn.pack(pady=8)
        
        # 清理选项
        self.clean_var = tk.BooleanVar(value=False)
        clean_check = tk.Checkbutton(self.btn_container, text="清理非代码文件", 
                                    variable=self.clean_var,
                                    bg="#e0e0e0", font=("Arial", 9),
                                    command=self._update_clean_description)
        clean_check.pack(pady=5)
        
        self.clean_desc = tk.Label(self.btn_container, 
                                  text="(删除图片、日志等非代码文件)", 
                                  bg="#e0e0e0", anchor="w", 
                                  font=("Arial", 8), fg="#666")
        self.clean_desc.pack(fill="x", padx=5, pady=(0, 5))
        
        # 分隔线
        tk.Frame(self.btn_container, height=2, bg="#cccccc").pack(fill="x", pady=10)

        # 工具选择框架
        tool_frame = tk.Frame(self.btn_container, bg="#e0e0e0")
        tool_frame.pack(fill="x", pady=5)

        row1 = tk.Frame(tool_frame, bg="#e0e0e0")
        row1.pack(fill="x")

        tk.Label(row1, text="工具:", bg="#e0e0e0",
                 font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 5))

        self.tool_combo = ttk.Combobox(row1, state="readonly")
        self.tool_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.tool_combo.bind('<<ComboboxSelected>>', self._on_tool_change)

        self.button_row = tk.Frame(tool_frame, bg="#e0e0e0")

        self.update_btn = tk.Button(self.button_row, text="⬇ 检查更新",
                                    command=self._check_for_updates,
                                    width=12, height=1,
                                    bg="#3498db", fg="white",
                                    font=("Arial", 8))
        self.settings_btn = tk.Button(self.button_row, text="⚙ 设置更新源",
                                      command=self._set_custom_url,
                                      width=12, height=1,
                                      bg="#95a5a6", fg="white",
                                      font=("Arial", 8, "bold"))

        btn_container_inner = tk.Frame(self.button_row, bg="#e0e0e0")
        btn_container_inner.pack(anchor=tk.CENTER)
        self.update_btn.pack(side=tk.LEFT, padx=5)
        self.settings_btn.pack(side=tk.LEFT, padx=5)

        # 自动转换和自动轮询放在一行
        options_frame = tk.Frame(self.btn_container, bg="#e0e0e0")
        options_frame.pack(fill="x", pady=5)

        # 自动转换pyc选项
        self.convert_pyc_var = tk.BooleanVar(value=True)
        convert_check = tk.Checkbutton(options_frame, text="自动转换pyc为py",
                                       variable=self.convert_pyc_var,
                                       bg="#e0e0e0", font=("Arial", 9))
        convert_check.pack(side=tk.LEFT, padx=(0, 10))

        # 自动轮询选项
        self.auto_retry_var = tk.BooleanVar(value=True)
        auto_retry_check = tk.Checkbutton(options_frame, text="轮询反编译工具",
                                          variable=self.auto_retry_var,
                                          bg="#e0e0e0", font=("Arial", 9))
        auto_retry_check.pack(side=tk.LEFT)

        # 转换说明
        self.convert_desc = tk.Label(self.btn_container,
                                     text="(推荐PyLingual)",
                                     bg="#e0e0e0", anchor="w",
                                     font=("Arial", 8), fg="#06d6a0")
        self.convert_desc.pack(fill="x", padx=5, pady=(0, 10))

        # 开始按钮
        self.start_btn = tk.Button(self.btn_container, text="▶ 开始解包",
                                   command=self._start_extraction,
                                   width=15, height=2, bg="#e74c3c", fg="white",
                                   font=("Arial", 12, "bold"))
        self.start_btn.pack(pady=10)

        # 打开目录按钮
        self.open_dir_btn = tk.Button(self.btn_container, text="📂 打开解包目录",
                                      command=self._open_output_dir,
                                      width=15, height=2, bg="#9b59b6", fg="white",
                                      font=("Arial", 12, "bold"))
        self.open_dir_btn.pack(pady=5)
        self.open_dir_btn.config(state=tk.DISABLED)
        
        # 右侧区域
        right_frame = tk.Frame(main_frame, bg="#ffffff", bd=2, relief=tk.GROOVE)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=10)
        
        # 代码预览区域
        preview_header = tk.Frame(right_frame, bg="white")
        preview_header.pack(padx=15, pady=(10, 5), fill=tk.X)
        
        preview_title = tk.Label(preview_header, text="📄 代码预览", font=("Arial", 10, "bold"),
                                 bg="white", fg="#2c3e50", anchor=tk.W)
        preview_title.pack(side=tk.LEFT)
        
        preview_toolbar = tk.Frame(preview_header, bg="white")
        preview_toolbar.pack(side=tk.RIGHT)
        
        export_preview_btn = tk.Button(preview_toolbar, text="💾 导出", command=self._export_preview_code,
                                       width=5, height=1, bg="#2ecc71", fg="white",
                                       font=("Arial", 8))
        export_preview_btn.pack(side=tk.LEFT, padx=2)
        
        copy_preview_btn = tk.Button(preview_toolbar, text="📋 复制", command=self._copy_preview_code,
                                     width=5, height=1, bg="#3498db", fg="white",
                                     font=("Arial", 8))
        copy_preview_btn.pack(side=tk.LEFT, padx=2)
        
        refresh_preview_btn = tk.Button(preview_toolbar, text="🔄 刷新", command=self._refresh_preview,
                                        width=5, height=1, bg="#9b59b6", fg="white",
                                        font=("Arial", 8))
        refresh_preview_btn.pack(side=tk.LEFT, padx=2)
        
        self.preview_text = scrolledtext.ScrolledText(right_frame, height=12, wrap=tk.NONE,
                                                       font=("Consolas", 9), bg="#1e1e1e", 
                                                       fg="#d4d4d4")
        self.preview_text.pack(padx=15, pady=(0, 10), fill=tk.BOTH, expand=True)
        
        # 日志区域
        log_header = tk.Frame(right_frame, bg="white")
        log_header.pack(padx=15, pady=(0, 5), fill=tk.X)
        
        log_title = tk.Label(log_header, text="📋 操作日志", font=("Arial", 10, "bold"),
                            bg="white", fg="#2c3e50", anchor=tk.W)
        log_title.pack(side=tk.LEFT)
        
        log_toolbar = tk.Frame(log_header, bg="white")
        log_toolbar.pack(side=tk.RIGHT)
        
        clear_btn = tk.Button(log_toolbar, text="🗑 清空", command=self._clear_log,
                             width=5, height=1, bg="#e74c3c", fg="white",
                             font=("Arial", 8))
        clear_btn.pack(side=tk.LEFT, padx=2)
        
        export_btn = tk.Button(log_toolbar, text="💾 导出", command=self._export_log,
                              width=5, height=1, bg="#3498db", fg="white",
                              font=("Arial", 8))
        export_btn.pack(side=tk.LEFT, padx=2)
        
        self.log_area = scrolledtext.ScrolledText(right_frame, height=8, wrap=tk.WORD,
                                                 font=("Consolas", 9), bg="#1e1e1e", 
                                                 fg="#d4d4d4")
        self.log_area.pack(padx=15, pady=(0, 10), fill=tk.BOTH, expand=True)
        
        # 进度条
        self.progress_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.progress_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 5))
        
        self.progress_label = tk.Label(self.progress_frame, text="进度: 0%", 
                                      bg="#f0f0f0", fg="#2c3e50", anchor=tk.W)
        self.progress_label.pack(fill=tk.X, padx=(0, 10), pady=(0, 5))
        
        self.progress = ttk.Progressbar(self.progress_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 5))
        
        # 状态栏
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, 
                             relief=tk.SUNKEN, bg="#2c3e50", fg="white", 
                             anchor=tk.W, font=("Arial", 10))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=5)
        
        # 初始化工具下拉菜单
        self.tool_combo['values'] = ["🌐 PyLingual ⭐⭐⭐⭐⭐"]
        self.tool_combo.set("🌐 PyLingual ⭐⭐⭐⭐⭐")
        self.tool_combo.config(state="readonly")
    
    def _update_resize_bar(self, event=None):
        if hasattr(self, 'resize_bar'):
            self.resize_bar.place(x=self.left_frame.winfo_width() - 3, y=0, 
                                 width=6, height=self.left_frame.winfo_height())
    
    def _start_resize(self, event):
        self.is_resizing = True
    
    def _resize_left_panel(self, event):
        if self.is_resizing:
            new_width = event.x_root - self.left_frame.winfo_rootx()
            min_width = int(self.root.winfo_width() * 0.15)
            max_width = int(self.root.winfo_width() * 0.35)
            if new_width < min_width:
                new_width = min_width
            if new_width > max_width:
                new_width = max_width
            
            self.left_panel_width = new_width
            self.left_frame.config(width=new_width)
            self._update_resize_bar()
    
    def _stop_resize(self, event):
        self.is_resizing = False
    
    def _update_progress(self, value, message=None):
        self.progress['value'] = value
        if message:
            self.progress_label.config(text=f"进度: {value}% - {message}")
        else:
            self.progress_label.config(text=f"进度: {value}%")
        self.root.update_idletasks()
    
    def _update_clean_description(self):
        if self.clean_var.get():
            self.clean_desc.config(text="(将删除图片、日志等非代码文件)")
        else:
            self.clean_desc.config(text="(保留所有文件，包括非代码文件)")
    
    def _update_convert_description(self):
        if self.convert_pyc_var.get():
            if hasattr(self, 'decompile_tool') and self.decompile_tool == "pylingual":
                self.convert_desc.config(text="(推荐使用PyLingual在线服务，支持混淆)", fg="#06d6a0")
            elif hasattr(self, 'decompile_tool') and self.decompile_tool in ["de4py", "pydumpck"]:
                self.convert_desc.config(text="(反混淆工具，专门处理混淆代码)", fg="#e74c3c")
            elif hasattr(self, 'decompile_tool') and self.decompile_tool == "pyc_decompiler":
                self.convert_desc.config(text="(使用本地PycDecompiler脚本)", fg="#9b59b6")
            else:
                self.convert_desc.config(text="(本地工具对混淆代码效果差)", fg="#ffd166")
        else:
            self.convert_desc.config(text="(不转换pyc文件)", fg="#666")
    
    def _update_info(self):
        """更新文件信息显示"""
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        
        info = f"📦 文件：{'未选择' if not self.file_path else os.path.basename(self.file_path)}\n"
        info += f"📁 输出目录：{self.output_dir if self.output_dir else '未设置（将使用默认路径）'}\n"
        info += f"🔧 反编译工具：{self.decompile_tool}\n"
        
        if self.file_path:
            file_size = os.path.getsize(self.file_path) if os.path.exists(self.file_path) else 0
            info += f"📊 文件大小：{file_size / 1024 / 1024:.2f} MB"
        
        self.preview_text.insert(tk.END, info)
        self.preview_text.config(state=tk.DISABLED)

    def _get_output_dir(self):
        """获取解包目录（带工具名称后缀）"""
        if not self.file_path:
            return None

        filename = os.path.basename(self.file_path)
        base_name = os.path.splitext(filename)[0]
        safe_name = re.sub(r'[<>:"/\\|?*]', '', base_name)

        extracted_dir = f"{safe_name}_extracted"

        if self.convert_pyc_var.get():
            tool_suffix = {
                "pylingual": "_pylingual",
                "pyc_decompiler": "_pycdec",
                "pycdc": "_pycdc",
                "py_cdec": "_pycdec",
                "de4py": "_de4py",
                "pychd": "_pychd",
                "pyobfus": "_pyobfus",
                "pydumpck": "_pydumpck",
                "uncompyle6": "_uncompyle6",
                "decompyle3": "_decompyle3"
            }.get(self.decompile_tool, "")

            if tool_suffix:
                extracted_dir = f"{safe_name}_extracted{tool_suffix}"

        return os.path.join(os.path.dirname(self.file_path), extracted_dir)
    
    def _select_file(self):
        path = filedialog.askopenfilename(filetypes=[("EXE文件", "*.exe"), ("所有文件", "*.*")])
        if path:
            self.file_path = path
            self._update_info()
            self.status_var.set(f"已选择文件：{os.path.basename(path)}")
            self._log(f"📁 选择文件：{path}", "info")
    
    def _select_output_dir(self):
        path = filedialog.askdirectory(title="选择解包输出目录")
        if path:
            self.output_dir = path
            self._update_info()
            self.status_var.set(f"输出目录：{path}")
            self._log(f"📂 设置输出目录：{path}", "info")
    
    def _open_output_dir(self):
        if self.output_dir and os.path.exists(self.output_dir):
            if sys.platform == 'win32':
                os.startfile(self.output_dir)
            elif sys.platform == 'darwin':
                subprocess.run(['open', self.output_dir])
            else:
                subprocess.run(['xdg-open', self.output_dir])
            self._log(f"📂 打开目录：{self.output_dir}", "info")
        else:
            self._show_error("解包目录不存在，请先完成解包操作")
    
    def _find_main_pyc_files(self, directory, exe_name):
        """只查找与exe同名的pyc文件"""
        main_pyc_files = []
        base_name = os.path.splitext(os.path.basename(exe_name))[0]
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.pyc'):
                    file_without_ext = os.path.splitext(file)[0]
                    if file_without_ext == base_name:
                        main_pyc_files.append(os.path.join(root, file))
                        self._log(f"找到主pyc文件: {file}", "info")
                        break
            if main_pyc_files:
                break
        
        return main_pyc_files
    
    def _convert_pyc_with_pylingual(self, pyc_file):
        """使用PyLingual在线服务转换"""
        try:
            self._log(f"  使用PyLingual在线服务反编译...", "info")
            
            headers = {
                "accept": "*/*",
                "origin": "https://pylingual.io",
                "referer": "https://pylingual.io/",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            with open(pyc_file, 'rb') as f:
                files = {
                    "file": (os.path.basename(pyc_file), f, "application/x-python-code"),
                    "fileName": (None, os.path.basename(pyc_file)),
                }
                response = requests.post(
                    "https://api.pylingual.io/upload",
                    headers=headers,
                    files=files,
                    timeout=30
                )
            
            if response.status_code != 200:
                raise Exception(f"上传失败: HTTP {response.status_code}")
            
            resp_json = response.json()
            identifier = resp_json.get("identifier")
            if not identifier:
                raise Exception("未获取到文件标识符")
            
            self._log(f"  文件已上传，等待反编译...", "info")
            
            wait_time = 0
            last_stage = ""
            while wait_time < 300:
                time.sleep(2)
                wait_time += 2
                
                progress_response = requests.get(
                    "https://api.pylingual.io/get_progress",
                    params={"identifier": identifier},
                    headers=headers,
                    timeout=10
                )
                
                stage = progress_response.json().get("stage")
                if stage != last_stage:
                    self._log(f"  反编译进度: {stage}", "info")
                    last_stage = stage
                    
                if stage == "done":
                    self._log(f"  反编译完成，耗时 {wait_time}秒", "success")
                    break
                elif stage == "error":
                    raise Exception("服务器反编译失败")
            else:
                raise Exception("反编译超时")
            
            result_response = requests.get(
                "https://api.pylingual.io/view_chimera",
                params={"identifier": identifier},
                headers=headers,
                timeout=30
            )
            
            decoded_code = result_response.json().get("editor_content", {}).get("file_raw_python", {}).get("editor_content")
            if not decoded_code:
                raise Exception("未获取到反编译代码")
            
            py_file = pyc_file[:-4] + '.py'
            with open(py_file, 'w', encoding='utf-8') as f:
                f.write(decoded_code)
            
            self._preview_code(py_file)
            return True, py_file
            
        except Exception as e:
            self._log(f"  PyLingual转换错误: {str(e)}", "warning")
            return False, None
    
    def _convert_pyc_with_pyc_decompiler(self, pyc_file):
        """使用外部的PycDecompiler.py转换"""
        if not self.has_pyc_decompiler or not self.pyc_decompiler_module:
            return False, None
        
        try:
            self._log(f"  使用本地 PycDecompiler 脚本反编译...", "info")
            
            if not hasattr(self.pyc_decompiler_module, 'decompile_pyc'):
                self._log("  PycDecompiler模块缺少decompile_pyc函数", "warning")
                return False, None
            
            temp_dir = os.path.join(os.path.dirname(pyc_file), "__temp_decompile__")
            os.makedirs(temp_dir, exist_ok=True)
            
            temp_pyc = os.path.join(temp_dir, os.path.basename(pyc_file))
            shutil.copy2(pyc_file, temp_pyc)
            
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                old_stdout = sys.stdout
                sys.stdout = self
                self.pyc_decompiler_module.decompile_pyc(temp_pyc)
                sys.stdout = old_stdout
                
                py_file = temp_pyc[:-4] + '.py'
                if os.path.exists(py_file):
                    target_py = pyc_file[:-4] + '.py'
                    shutil.copy2(py_file, target_py)
                    os.chdir(original_cwd)
                    shutil.rmtree(temp_dir)
                    self._preview_code(target_py)
                    return True, target_py
            except Exception as e:
                self._log(f"  PycDecompiler执行错误: {str(e)}", "warning")
            finally:
                sys.stdout = old_stdout
                os.chdir(original_cwd)
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
            
            return False, None
        except Exception as e:
            self._log(f"  PycDecompiler转换错误: {str(e)}", "warning")
            return False, None
    
    def _convert_pyc_with_de4py(self, pyc_file):
        """使用De4py反混淆"""
        tool_path = self.available_tools.get("de4py")
        if not tool_path:
            self._log("  De4py未安装，请运行: pip install de4py", "warning")
            return False, None
        
        try:
            py_file = pyc_file[:-4] + '.py'
            self._log(f"  使用De4py反混淆...", "info")
            
            cmd = [sys.executable, '-m', 'de4py', pyc_file, '-o', py_file]
            
            result = subprocess.run(cmd, capture_output=True, timeout=120,
                                   text=True, encoding='utf-8', errors='ignore')
            
            if result.returncode == 0 and os.path.exists(py_file):
                self._preview_code(py_file)
                self._log(f"  De4py反混淆成功", "success")
                return True, py_file
            else:
                self._log(f"  De4py反混淆失败: {result.stderr[:200] if result.stderr else '未知错误'}", "warning")
                return False, None
        except Exception as e:
            self._log(f"  De4py反混淆错误: {str(e)}", "warning")
            return False, None
    
    def _convert_pyc_with_pydumpck(self, pyc_file):
        """使用PyDumpck反混淆"""
        tool_path = self.available_tools.get("pydumpck")
        if not tool_path:
            self._log("  PyDumpck未安装，请运行: pip install pydumpck", "warning")
            return False, None
        
        try:
            py_file = pyc_file[:-4] + '.py'
            self._log(f"  使用PyDumpck反混淆...", "info")
            
            cmd = [sys.executable, '-m', 'pydumpck', pyc_file, '-o', py_file]
            
            result = subprocess.run(cmd, capture_output=True, timeout=120,
                                   text=True, encoding='utf-8', errors='ignore')
            
            if result.returncode == 0 and os.path.exists(py_file):
                self._preview_code(py_file)
                self._log(f"  PyDumpck反混淆成功", "success")
                return True, py_file
            else:
                self._log(f"  PyDumpck反混淆失败: {result.stderr[:200] if result.stderr else '未知错误'}", "warning")
                return False, None
        except Exception as e:
            self._log(f"  PyDumpck反混淆错误: {str(e)}", "warning")
            return False, None

    def _convert_pyc_with_pychd(self, pyc_file):
        """使用PyChD反编译（支持LLM辅助）"""
        tool_path = self.available_tools.get("pychd")
        if not tool_path:
            self._log("  PyChD未安装，请运行: pip install pychd", "warning")
            return False, None

        try:
            py_file = pyc_file[:-4] + '.py'
            self._log(f"  使用PyChD反编译（混合规则+LLM）...", "info")

            if isinstance(tool_path, str) and tool_path.startswith("python -m"):
                cmd = [sys.executable, '-m', 'pychd', pyc_file, '-o', py_file]
            else:
                cmd = [tool_path, pyc_file, '-o', py_file]

            result = subprocess.run(cmd, capture_output=True, timeout=180,
                                    text=True, encoding='utf-8', errors='ignore')

            if result.returncode == 0 and os.path.exists(py_file):
                # 检查文件是否有内容
                if os.path.getsize(py_file) > 0:
                    self._preview_code(py_file)
                    self._log(f"  PyChD反编译成功", "success")
                    return True, py_file

            # 如果输出到stdout
            if result.stdout and len(result.stdout.strip()) > 0:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                self._preview_code(py_file)
                self._log(f"  PyChD反编译成功（从stdout）", "success")
                return True, py_file

            self._log(f"  PyChD反编译失败", "warning")
            return False, None
        except Exception as e:
            self._log(f"  PyChD反编译错误: {str(e)}", "warning")
            return False, None

    def _convert_pyc_with_pyobfus(self, pyc_file):
        """使用PyObfus反混淆"""
        tool_path = self.available_tools.get("pyobfus")
        if not tool_path:
            self._log("  PyObfus未安装，请运行: pip install pyobfus", "warning")
            return False, None

        try:
            py_file = pyc_file[:-4] + '.py'
            self._log(f"  使用PyObfus反混淆（AST转换）...", "info")

            if isinstance(tool_path, str) and tool_path.startswith("python -m"):
                cmd = [sys.executable, '-m', 'pyobfus', pyc_file, '-o', py_file]
            else:
                cmd = [tool_path, pyc_file, '-o', py_file]

            result = subprocess.run(cmd, capture_output=True, timeout=120,
                                    text=True, encoding='utf-8', errors='ignore')

            if result.returncode == 0 and os.path.exists(py_file):
                self._preview_code(py_file)
                self._log(f"  PyObfus反混淆成功", "success")
                return True, py_file
            elif result.stdout and len(result.stdout.strip()) > 0:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                self._preview_code(py_file)
                self._log(f"  PyObfus反混淆成功（从stdout）", "success")
                return True, py_file

            self._log(f"  PyObfus反混淆失败", "warning")
            return False, None
        except Exception as e:
            self._log(f"  PyObfus反混淆错误: {str(e)}", "warning")
            return False, None
    def _convert_pyc_with_pycdc(self, pyc_file):
        """使用pycdc转换"""
        tool_path = self.available_tools.get("pycdc")
        if not tool_path:
            return False, None
        
        try:
            py_file = pyc_file[:-4] + '.py'
            
            if isinstance(tool_path, str) and tool_path.startswith("python -m"):
                cmd = [sys.executable, '-m', 'pycdc', pyc_file]
            else:
                cmd = [tool_path, pyc_file]
            
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            
            if result.returncode == 0 and result.stdout:
                output_text = None
                for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
                    try:
                        output_text = result.stdout.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if output_text is None:
                    output_text = result.stdout.decode('utf-8', errors='ignore')
                
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(output_text)
                self._preview_code(py_file)
                return True, py_file
            return False, None
        except Exception as e:
            self._log(f"  pycdc转换错误: {str(e)}", "warning")
            return False, None
    
    def _convert_pyc_with_py_cdec(self, pyc_file):
        """使用py-cdec转换"""
        tool_path = self.available_tools.get("py_cdec")
        if not tool_path:
            return False, None
        
        try:
            py_file = pyc_file[:-4] + '.py'
            
            if isinstance(tool_path, str) and tool_path.startswith("python -m"):
                cmd = [sys.executable, '-m', 'cdec', pyc_file, '-o', py_file]
            else:
                cmd = [tool_path, pyc_file, '-o', py_file]
            
            result = subprocess.run(cmd, capture_output=True, timeout=60,
                                   text=True, encoding='utf-8', errors='ignore')
            
            if result.returncode == 0 and os.path.exists(py_file):
                self._preview_code(py_file)
                return True, py_file
            elif result.stdout:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                self._preview_code(py_file)
                return True, py_file
            return False, None
        except Exception as e:
            self._log(f"  py-cdec转换错误: {str(e)}", "warning")
            return False, None
    
    def _convert_pyc_with_uncompyle6(self, pyc_file):
        """使用uncompyle6转换"""
        tool_path = self.available_tools.get("uncompyle6")
        if not tool_path:
            return False, None
        
        try:
            py_file = pyc_file[:-4] + '.py'
            
            if isinstance(tool_path, str) and tool_path.startswith("python -m"):
                cmd = [sys.executable, '-m', 'uncompyle6', '-o', os.path.dirname(pyc_file), pyc_file]
            else:
                cmd = [tool_path, '-o', os.path.dirname(pyc_file), pyc_file]
            
            result = subprocess.run(cmd, capture_output=True, timeout=60,
                                   text=True, encoding='utf-8', errors='ignore')
            
            if result.returncode == 0:
                self._preview_code(py_file)
                return True, py_file
            return False, None
        except Exception as e:
            self._log(f"  uncompyle6转换错误: {str(e)}", "warning")
            return False, None
    
    def _convert_pyc_with_decompyle3(self, pyc_file):
        """使用decompyle3转换"""
        tool_path = self.available_tools.get("decompyle3")
        if not tool_path:
            return False, None
        
        try:
            py_file = pyc_file[:-4] + '.py'
            
            if isinstance(tool_path, str) and tool_path.startswith("python -m"):
                cmd = [sys.executable, '-m', 'decompyle3', pyc_file]
            else:
                cmd = [tool_path, pyc_file]
            
            result = subprocess.run(cmd, capture_output=True, timeout=60,
                                   text=True, encoding='utf-8', errors='ignore')
            
            if result.returncode == 0 and result.stdout:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                self._preview_code(py_file)
                return True, py_file
            return False, None
        except Exception as e:
            self._log(f"  decompyle3转换错误: {str(e)}", "warning")
            return False, None
    
    def _convert_pyc_to_py(self, pyc_file):
        """使用选定的工具转换"""
        tool = self.decompile_tool.lower()
        
        if tool == "pylingual":
            return self._convert_pyc_with_pylingual(pyc_file)
        elif tool == "pyc_decompiler":
            return self._convert_pyc_with_pyc_decompiler(pyc_file)
        elif tool == "de4py":
            return self._convert_pyc_with_de4py(pyc_file)
        elif tool == "pychd":
            return self._convert_pyc_with_pychd(pyc_file)
        elif tool == "pyobfus":
            return self._convert_pyc_with_pyobfus(pyc_file)
        elif tool == "pydumpck":
            return self._convert_pyc_with_pydumpck(pyc_file)
        elif tool == "pycdc":
            return self._convert_pyc_with_pycdc(pyc_file)
        elif tool == "py_cdec":
            return self._convert_pyc_with_py_cdec(pyc_file)
        elif tool == "uncompyle6":
            return self._convert_pyc_with_uncompyle6(pyc_file)
        elif tool == "decompyle3":
            return self._convert_pyc_with_decompyle3(pyc_file)
        else:
            self._log(f"未知的反编译工具: {tool}", "warning")
            return False, None

    def _convert_main_pyc_files(self, directory):
        """转换主要的pyc文件，支持自动轮询"""
        if not self.available_tools:
            self._log("未找到任何反编译工具，跳过pyc转换", "warning")
            return 0, 0

        # 获取当前选择的工具
        current_tool = self.decompile_tool
        tool_info = self.decompile_tools.get(current_tool, {})
        quality = tool_info.get("quality", "")

        self._log(f"使用工具: {current_tool} {quality}", "info")
        self._log(f"  说明: {tool_info.get('description', '')}", "info")

        main_pyc_files = self._find_main_pyc_files(directory, self.file_path)

        if not main_pyc_files:
            self._log("未找到主pyc文件，跳过转换", "warning")
            return 0, 0

        self._log(f"找到 {len(main_pyc_files)} 个主pyc文件待转换", "info")
        for pyc_file in main_pyc_files:
            rel_path = os.path.relpath(pyc_file, directory)
            self._log(f"  - {rel_path}", "info")

        success_count = 0
        fail_count = 0
        success_tool = None  # 记录成功使用的工具

        # 定义工具轮询顺序（按效果排序）
        tool_priority = [
            "pylingual",
            "pychd",
            "pyobfus",
            "de4py",
            "pydumpck",
            "pyc_decompiler",
            "pycdc",
            "py_cdec",
            "uncompyle6",
            "decompyle3"
        ]

        for i, pyc_file in enumerate(main_pyc_files):
            self._update_progress(95 + int((i / len(main_pyc_files)) * 4),
                                  f"转换 ({i + 1}/{len(main_pyc_files)})")

            success = False
            py_result = None
            used_tool = None

            # 首先尝试用户选择的工具
            self._log(f"  尝试使用 {self.decompile_tool} 转换...", "info")
            success, py_result = self._convert_pyc_to_py(pyc_file)
            if success:
                used_tool = self.decompile_tool

            # 如果失败且启用了自动轮询
            if not success and self.auto_retry_var.get():
                self._log(f"  ⚠ {self.decompile_tool} 转换失败，开始自动轮询其他工具...", "warning")

                for tool_key in tool_priority:
                    if tool_key == self.decompile_tool:
                        continue
                    if tool_key not in self.available_tools:
                        continue
                    if self.available_tools.get(tool_key) is None:
                        continue

                    # 保存当前工具，临时切换
                    original_tool = self.decompile_tool
                    self.decompile_tool = tool_key

                    self._log(f"  尝试使用 {tool_key} 转换...", "info")
                    success, py_result = self._convert_pyc_to_py(pyc_file)

                    # 恢复原工具
                    self.decompile_tool = original_tool

                    if success:
                        used_tool = tool_key
                        self._log(f"  ✓ {tool_key} 转换成功！", "success")
                        break

                if not success:
                    self._log(f"  ✗ 所有可用工具均转换失败", "error")

            if success:
                success_count += 1
                success_tool = used_tool
                rel_path = os.path.relpath(py_result, directory)
                self._log(f"✓ 转换成功: {rel_path} (使用 {used_tool})", "success")
            else:
                fail_count += 1
                rel_path = os.path.relpath(pyc_file, directory)
                self._log(f"✗ 转换失败: {rel_path}", "warning")

        # 如果成功使用了不同于原选择的工具，重命名目录
        if success_tool and success_tool != self.decompile_tool:
            old_dir = directory
            # 获取基础文件名
            filename = os.path.basename(self.file_path)
            base_name = os.path.splitext(filename)[0]
            safe_name = re.sub(r'[<>:"/\\|?*]', '', base_name)

            # 新后缀
            tool_suffix_map = {
                "pylingual": "_pylingual",
                "pyc_decompiler": "_pycdec",
                "pycdc": "_pycdc",
                "py_cdec": "_pycdec",
                "de4py": "_de4py",
                "pychd": "_pychd",
                "pyobfus": "_pyobfus",
                "pydumpck": "_pydumpck",
                "uncompyle6": "_uncompyle6",
                "decompyle3": "_decompyle3"
            }
            suffix = tool_suffix_map.get(success_tool, "")
            new_dir = os.path.join(os.path.dirname(old_dir), f"{safe_name}_extracted{suffix}")

            # 如果新旧目录不同，重命名
            if old_dir != new_dir and os.path.exists(old_dir):
                try:
                    # 如果新目录已存在，先删除
                    if os.path.exists(new_dir):
                        shutil.rmtree(new_dir)
                    os.rename(old_dir, new_dir)
                    self.output_dir = new_dir
                    self._log(f"📁 目录已重命名: {os.path.basename(old_dir)} → {os.path.basename(new_dir)}", "success")
                    self._update_info()
                except Exception as e:
                    self._log(f"目录重命名失败: {str(e)}", "warning")

        return success_count, fail_count
    
    def _start_extraction(self):
        """启动解包流程"""
        if not self.file_path:
            self._show_error("请先选择或拖拽待解包的EXE文件")
            return
        
        if not os.path.exists(self.file_path):
            self._show_error("选择的文件不存在，请重新选择")
            return
        
        # 重置输出目录
        self.output_dir = ""
        self._update_info()
        
        self._update_progress(0, "准备开始解包")
        self.start_btn.config(state=tk.DISABLED)
        self.open_dir_btn.config(state=tk.DISABLED)
        self.status_var.set("解包中...请稍候")
        self._log("开始解包操作", "info")
        self.extraction_active = True
        
        threading.Thread(target=self._perform_extraction, daemon=True).start()
    
    def _perform_extraction(self):
        """实际解包操作"""
        try:
            self._update_progress(10, "分析文件结构...")
            time.sleep(0.3)
            
            final_dir = self._get_output_dir()
            if not final_dir:
                raise ValueError("输出目录未正确生成")
            
            # 如果目录已存在，直接删除重建
            if os.path.exists(final_dir):
                try:
                    shutil.rmtree(final_dir)
                    self._log(f"已清理旧目录: {final_dir}", "info")
                except Exception as e:
                    self._log(f"清理旧目录失败: {str(e)}，使用带时间戳的目录", "warning")
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    final_dir = f"{final_dir}_{timestamp}"
                    self._log(f"使用新目录: {final_dir}", "info")
            
            self.output_dir = final_dir
            self._update_info()
            os.makedirs(final_dir, exist_ok=True)
            self._log(f"创建输出目录：{final_dir}", "info")
            
            if self.convert_pyc_var.get():
                self._log(f"使用工具: {self.decompile_tool}", "info")
            
            self._update_progress(30, "提取文件中...")
            
            try:
                pyinstxtractorcn.dcp(self.file_path, final_dir)
            except Exception as e:
                if "WinError 206" in str(e):
                    self._log(f"⚠ 路径过长错误，尝试使用短路径...", "warning")
                    # 尝试使用8.3短文件名
                    import ctypes
                    GetShortPathName = ctypes.windll.kernel32.GetShortPathNameW
                    short_path = ctypes.create_unicode_buffer(260)
                    GetShortPathName(final_dir, short_path, 260)
                    if short_path.value:
                        final_dir = short_path.value
                        self._log(f"使用短路径: {final_dir}", "info")
                        pyinstxtractorcn.dcp(self.file_path, final_dir)
                    else:
                        raise
                else:
                    raise
            
            self._update_progress(80, "解包完成，正在处理后续操作...")
            
            if self.clean_var.get():
                self._clean_non_code_files(final_dir)
                self._log("已清理非代码文件", "info")
            
            success_count = 0
            fail_count = 0
            if self.convert_pyc_var.get() and self.available_tools:
                self._update_progress(90, "正在转换pyc文件...")
                success_count, fail_count = self._convert_main_pyc_files(final_dir)
                if success_count > 0:
                    self._log(f"转换完成: 成功 {success_count} 个, 失败 {fail_count} 个", "success")
            
            self._update_progress(100, "解包完成！")
            self._log(f"解包完成！文件保存至：{final_dir}", "success")
            
            msg = f"解包完成！\n保存位置：{final_dir}"
            if success_count > 0:
                msg += f"\n成功转换 {success_count} 个pyc文件"
            if fail_count > 0:
                msg += f"\n{fail_count} 个pyc文件转换失败"
            
            self._show_success(msg)
            self.root.after(0, lambda: self.open_dir_btn.config(state=tk.NORMAL))
            
        except pyinstxtractorcn.InvalidFileError:
            self._show_error("无效的PyInstaller打包文件")
        except Exception as e:
            self._show_error(f"解包失败：{str(e)}")
        finally:
            self.extraction_active = False
            self.start_btn.config(state=tk.NORMAL)
    
    def _clean_non_code_files(self, output_dir):
        try:
            non_code_exts = {
                '.tmp', '.log', '.bak', '.png', '.jpg', '.jpeg', 
                '.gif', '.bmp', '.ico', '.svg', '.mp3', '.wav',
                '.mp4', '.avi', '.mov', '.pdf', '.doc', '.docx',
                '.xls', '.xlsx', '.json', '.xml', '.cache', '.db',
                '.ttf', '.woff', '.woff2', '.eot', '.otf'
            }
            
            count = 0
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in non_code_exts:
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                            count += 1
                        except Exception as e:
                            pass
            
            if count > 0:
                self._log(f"已清理 {count} 个非代码文件", "info")
            return True
        except Exception as e:
            return False
    
    def _show_error(self, msg):
        self.status_var.set(f"错误：{msg}")
        self._log(f"错误：{msg}", "error")
        self.root.config(bg="#ffdddd")
        self.root.after(2000, lambda: self.root.config(bg="#f0f0f0"))
        self._update_progress(0, "解包失败")
        self.start_btn.config(state=tk.NORMAL)
    
    def _show_success(self, msg):
        short_msg = msg.split('\n')[0]
        self.status_var.set(f"成功：{short_msg}")
        self.root.config(bg="#d4edda")
        self.root.after(2000, lambda: self.root.config(bg="#f0f0f0"))
        messagebox.showinfo("操作成功", msg)
    
    def _log(self, msg, level="info"):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        
        color_map = {
            "info": "#d4d4d4",
            "warning": "#ffd166",
            "error": "#ff6b6b",
            "success": "#06d6a0"
        }
        color = color_map.get(level, "#d4d4d4")
        
        def _log_to_ui():
            tag_name = f"tag_{timestamp}_{int(time.time()*1000)}"
            self.log_area.tag_config(tag_name, foreground=color)
            self.log_area.insert(tk.END, f"{timestamp} {msg}\n", tag_name)
            self.log_area.see(tk.END)
        
        self.root.after(0, _log_to_ui)
    
    def write(self, text):
        if text.strip() != '':
            self._log(text.rstrip(), "info")
    
    def flush(self):
        pass

if __name__ == "__main__":
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
        #print("✓ 拖拽功能已启用")
    except ImportError:
        #print("提示：安装 tkinterdnd2 可支持文件拖拽功能")
        #print("安装命令：pip install tkinterdnd2")
        root = tk.Tk()

# AUTO_INJECTED_ICON
if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(__file__)
_ip = os.path.join(_base, "icon.ico")
if os.path.exists(_ip):
    try: self.root.iconbitmap(_ip)
    except: pass
# END AUTO_INJECTED_ICON

    
    app = PyInstxtractorCN_GUI(root)
    root.mainloop()