#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import time
import subprocess
import shutil
import importlib.util
import requests
from datetime import datetime

class PyInstxtractorCN_CLI:
    def __init__(self):
        self.file_path = ""
        self.output_dir = ""
        self.decompile_tool = "pylingual"
        self.auto_retry = True
        self.auto_fix = True
        self.available_tools = {}
        self.has_pyc_decompiler = False
        self.pyc_decompiler_module = None
        
        self.tool_priority = ["pylingual", "pyc_decompiler", "pydumpck", "pycdc", "py_cdec", "uncompyle6", "decompyle3"]
        
        self.decompile_tools = {
            "pylingual": {"name": "PyLingual", "desc": "在线反编译", "quality": "⭐⭐⭐⭐⭐"},
            "pyc_decompiler": {"name": "PycDecompiler", "desc": "本地脚本", "quality": "⭐⭐⭐⭐"},
            "pydumpck": {"name": "PyDumpck", "desc": "多线程", "quality": "⭐⭐⭐"},
            "pycdc": {"name": "pycdc", "desc": "C++编写", "quality": "⭐⭐⭐"},
            "py_cdec": {"name": "py-cdec", "desc": "pip install", "quality": "⭐⭐⭐"},
            "uncompyle6": {"name": "uncompyle6", "desc": "传统反编译", "quality": "⭐⭐"},
            "decompyle3": {"name": "decompyle3", "desc": "Python3专用", "quality": "⭐⭐"}
        }
        
        self._check_dependencies()
        self._import_pyc_decompiler()
        self._find_available_tools()
        self._auto_detect_exe()
    
    def _log(self, msg, level="info"):
        ts = datetime.now().strftime("[%H:%M:%S]")
        colors = {"info": "\033[0m", "success": "\033[92m", "warning": "\033[93m", "error": "\033[91m"}
        print(f"{colors.get(level, '\033[0m')}{ts} {msg}\033[0m")
    
    def _check_dependencies(self):
        deps = {"pyinstxtractorcn": "pyinstxtractorcn", "requests": "requests"}
        for module, package in deps.items():
            if importlib.util.find_spec(module) is None:
                self._log(f"安装 {module}...", "warning")
                subprocess.run([sys.executable, "-m", "pip", "install", package], capture_output=True)
    
    def _import_pyc_decompiler(self):
        for path in [os.path.join(os.getcwd(), "PycDecompiler.py")]:
            if os.path.exists(path):
                try:
                    spec = importlib.util.spec_from_file_location("PycDecompiler", path)
                    if spec:
                        self.pyc_decompiler_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(self.pyc_decompiler_module)
                        self.has_pyc_decompiler = True
                        self._log("✓ 加载 PycDecompiler.py", "success")
                        return
                except: pass
    
    def _find_available_tools(self):
        self.available_tools = {"pylingual": True}
        if self.has_pyc_decompiler:
            self.available_tools["pyc_decompiler"] = True
        
        # 检查并安装工具
        for tool, pip_name in [("pycdc", None), ("py_cdec", "py-cdec"), 
                                ("pydumpck", "pydumpck"), ("uncompyle6", "uncompyle6"),
                                ("decompyle3", "decompyle3")]:
            if shutil.which(tool):
                self.available_tools[tool] = True
                self._log(f"✓ 找到 {tool}", "success")
            elif pip_name:
                self._log(f"尝试安装 {tool}...", "info")
                r = subprocess.run([sys.executable, "-m", "pip", "install", pip_name], capture_output=True)
                if r.returncode == 0 and shutil.which(tool):
                    self.available_tools[tool] = True
                    self._log(f"✓ {tool} 安装成功", "success")
                else:
                    self.available_tools[tool] = False
                    self._log(f"✗ {tool} 安装失败: pip install {pip_name}", "warning")
            else:
                self.available_tools[tool] = False
                if tool == "pycdc":
                    self._log(f"✗ {tool} 未找到，需手动编译安装", "warning")
    
    def _get_available_names(self):
        names = []
        for k, v in self.decompile_tools.items():
            if self.available_tools.get(k, False):
                names.append(v['name'])
        return ', '.join(names)
    
    def _list_exe_files(self):
        return [f for f in os.listdir('.') if f.lower().endswith('.exe') and os.path.isfile(f)]

    def _auto_detect_exe(self):
        """自动检测exe文件，多个时默认选第一个"""
        exes = self._list_exe_files()
        if len(exes) >= 1:
            self.file_path = os.path.abspath(exes[0])
            if len(exes) == 1:
                self._log(f"自动选择: {os.path.basename(self.file_path)}", "success")
            else:
                self._log(f"检测到 {len(exes)} 个exe，默认选第一个: {os.path.basename(self.file_path)}", "info")
                self._log("如需更换请按1重新选择", "info")

    def _select_file(self):
        """选择EXE文件"""
        exes = self._list_exe_files()

        print("\n" + "=" * 20)
        print("选择EXE")
        print("=" * 20)
        print(f"\n当前目录: {os.getcwd()}")

        if exes:
            print("\n当前目录下的exe文件:")
            for i, f in enumerate(exes, 1):
                size = os.path.getsize(f) / 1024 / 1024
                mark = " [当前]" if self.file_path and os.path.basename(self.file_path) == f else ""
                print(f"{i}. {f} ({size:.1f}MB){mark}")
            print(f"{len(exes) + 1}. 浏览其他目录")
            print(f"{len(exes) + 2}. 手动输入路径")
            print("0. 取消")

            # 显示当前选中的文件
            if self.file_path:
                print(f"\n当前选中: {os.path.basename(self.file_path)}")

            ch = input(f"\n请选择 (1-{len(exes) + 2}/0, 回车保持当前): ").strip()

            if ch == '':
                if self.file_path:
                    self._log(f"保持当前: {os.path.basename(self.file_path)}", "info")
                else:
                    self._log("未选择文件", "warning")
                return
            elif ch == '0':
                return
            elif ch.isdigit():
                ch = int(ch)
                if 1 <= ch <= len(exes):
                    self.file_path = os.path.abspath(exes[ch - 1])
                    self._log(f"已选择: {os.path.basename(self.file_path)}", "success")
                elif ch == len(exes) + 1:
                    self._browse_directory()
                elif ch == len(exes) + 2:
                    p = input("请输入完整路径: ").strip().strip('"')
                    if p and os.path.exists(p) and p.lower().endswith('.exe'):
                        self.file_path = os.path.abspath(p)
                        self._log(f"已选择: {os.path.basename(self.file_path)}", "success")
                    else:
                        self._log("文件不存在或不是exe文件", "error")
                else:
                    self._log("无效选择", "error")
            else:
                self._log("无效输入", "error")
        else:
            print("\n当前目录下没有exe文件")
            print("1. 浏览其他目录")
            print("2. 手动输入路径")
            print("0. 取消")
            ch = input("\n请选择: ").strip()
            if ch == '1':
                self._browse_directory()
            elif ch == '2':
                p = input("请输入exe路径: ").strip().strip('"')
                if p and os.path.exists(p) and p.lower().endswith('.exe'):
                    self.file_path = os.path.abspath(p)
                    self._log(f"已选择: {os.path.basename(self.file_path)}", "success")
                else:
                    self._log("文件不存在或不是exe文件", "error")
            else:
                self._log("未选择文件", "warning")

    def _browse_directory(self):
        """浏览目录选择文件"""
        current = os.getcwd()
        while True:
            print(f"\n当前目录: {current}")
            print("=" * 20)

            # 列出目录
            items = []
            # 返回上级
            items.append("..")

            # 列出子目录
            dirs = []
            files = []
            try:
                for f in os.listdir(current):
                    full = os.path.join(current, f)
                    if os.path.isdir(full):
                        dirs.append(f)
                    elif f.lower().endswith('.exe'):
                        files.append(f)
            except:
                pass

            dirs.sort()
            files.sort()

            for d in dirs:
                items.append(f"📁 {d}")
            for f in files:
                size = os.path.getsize(os.path.join(current, f)) / 1024 / 1024
                items.append(f"📄 {f} ({size:.1f}MB)")

            for i, item in enumerate(items, 1):
                print(f"{i}. {item}")
            print("0. 返回")

            ch = input("\n请选择: ").strip()
            if ch == '0':
                break
            elif ch.isdigit():
                idx = int(ch) - 1
                if 0 <= idx < len(items):
                    selected = items[idx]
                    if selected == "..":
                        current = os.path.dirname(current)
                    elif selected.startswith("📁 "):
                        current = os.path.join(current, selected[2:])
                    elif selected.startswith("📄 "):
                        # 提取文件名
                        fname = selected[2:].split(' (')[0]
                        self.file_path = os.path.join(current, fname)
                        self._log(f"已选择: {os.path.basename(self.file_path)}", "success")
                        return
                else:
                    self._log("无效选择", "error")
            else:
                self._log("无效输入", "error")
    
    def _get_output_dir(self):
        if not self.file_path:
            return None
        base = os.path.splitext(os.path.basename(self.file_path))[0]
        safe = re.sub(r'[<>:"/\\|?*]', '', base)
        out = f"{safe}_extracted"
        return os.path.join(self.output_dir, out) if self.output_dir else os.path.join(os.path.dirname(self.file_path), out)
    
    def _output_dir_setup(self):
        default = self._get_output_dir()
        if default:
            print(f"默认: {default}")
        p = input("目录(回车默认): ").strip().strip('"')
        if p:
            self.output_dir = p
        else:
            self.output_dir = ""
    
    def _select_tool(self):
        print("\n" + "=" * 20)
        print("选择工具")
        print("=" * 20)
        tools = []
        for i, (k, v) in enumerate(self.decompile_tools.items(), 1):
            ok = "✓" if self.available_tools.get(k, False) else "✗"
            print(f"{i}. {ok} {v['name']} {v['quality']}")
            tools.append(k)
        print("0. 返回")
        ch = input(": ").strip()
        if ch.isdigit():
            ch = int(ch)
            if 1 <= ch <= len(tools):
                self.decompile_tool = tools[ch-1]
                self._log(f"已切: {self.decompile_tool}", "success")
    
    def _smart_fix_code(self, file_path):
        if not os.path.exists(file_path):
            return
        self._log("修复代码...", "info")
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        code = re.sub(r'\.\s*\+\s*', '.', code)
        code = re.sub(r'self\.\s*\+\s*_', 'self._', code)
        code = re.sub(r'\btrue\b', 'True', code, flags=re.I)
        code = re.sub(r'\bfalse\b', 'False', code, flags=re.I)
        code = re.sub(r'\bnone\b', 'None', code, flags=re.I)
        code = re.sub(r'\b_init_\b', '__init__', code)
        code = re.sub(r'\b_str_\b', '__str__', code)
        code = re.sub(r'\b_name_\b', '__name__', code)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        self._log("✓ 修复完成", "success")
    
    def _decompile_pylingual(self, pyc_file):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            with open(pyc_file, 'rb') as f:
                r = requests.post("https://api.pylingual.io/upload", headers=headers, 
                                 files={"file": (os.path.basename(pyc_file), f)}, timeout=30)
            if r.status_code != 200:
                return False, None
            pid = r.json().get("identifier")
            if not pid:
                return False, None
            for _ in range(30):
                time.sleep(2)
                p = requests.get("https://api.pylingual.io/get_progress", params={"identifier": pid}, headers=headers)
                if p.json().get("stage") == "done":
                    break
            res = requests.get("https://api.pylingual.io/view_chimera", params={"identifier": pid}, headers=headers)
            code = res.json().get("editor_content", {}).get("file_raw_python", {}).get("editor_content")
            if code:
                py_file = pyc_file[:-4] + '.py'
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(code)
                return True, py_file
            return False, None
        except:
            return False, None
    
    def _decompile_pyc_decompiler(self, pyc_file):
        if not self.pyc_decompiler_module:
            return False, None
        try:
            old = sys.stdout
            sys.stdout = sys.__stdout__
            self.pyc_decompiler_module.decompile_pyc(pyc_file)
            sys.stdout = old
            py_file = pyc_file[:-4] + '.py'
            return (True, py_file) if os.path.exists(py_file) else (False, None)
        except:
            return False, None
    
    def _decompile_pycdc(self, pyc_file):
        try:
            py_file = pyc_file[:-4] + '.py'
            r = subprocess.run(['pycdc', pyc_file], capture_output=True, timeout=30)
            if r.returncode == 0 and r.stdout:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(r.stdout.decode('utf-8', errors='ignore'))
                return True, py_file
            return False, None
        except:
            return False, None
    
    def _decompile_py_cdec(self, pyc_file):
        try:
            py_file = pyc_file[:-4] + '.py'
            r = subprocess.run(['py-cdec', pyc_file, '-o', py_file], capture_output=True, timeout=30)
            if r.returncode == 0 and os.path.exists(py_file):
                return True, py_file
            return False, None
        except:
            return False, None
    
    def _decompile_pydumpck(self, pyc_file):
        try:
            py_file = pyc_file[:-4] + '.py'
            r = subprocess.run(['pydumpck', pyc_file, '-o', py_file], capture_output=True, timeout=60)
            if r.returncode == 0 and os.path.exists(py_file):
                return True, py_file
            return False, None
        except:
            return False, None
    
    def _decompile_uncompyle6(self, pyc_file):
        try:
            py_file = pyc_file[:-4] + '.py'
            r = subprocess.run(['uncompyle6', pyc_file], capture_output=True, timeout=30)
            if r.returncode == 0 and r.stdout:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(r.stdout)
                return True, py_file
            return False, None
        except:
            return False, None
    
    def _decompile_decompyle3(self, pyc_file):
        try:
            py_file = pyc_file[:-4] + '.py'
            r = subprocess.run(['decompyle3', pyc_file], capture_output=True, timeout=30)
            if r.returncode == 0 and r.stdout:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(r.stdout)
                return True, py_file
            return False, None
        except:
            return False, None
    
    def _decompile_with_tool(self, pyc_file, tool):
        self._log(f"尝试 {tool}...", "info")
        if tool == "pylingual":
            return self._decompile_pylingual(pyc_file)
        elif tool == "pyc_decompiler" and self.has_pyc_decompiler:
            return self._decompile_pyc_decompiler(pyc_file)
        elif tool == "pycdc":
            return self._decompile_pycdc(pyc_file)
        elif tool == "py_cdec":
            return self._decompile_py_cdec(pyc_file)
        elif tool == "pydumpck":
            return self._decompile_pydumpck(pyc_file)
        elif tool == "uncompyle6":
            return self._decompile_uncompyle6(pyc_file)
        elif tool == "decompyle3":
            return self._decompile_decompyle3(pyc_file)
        return False, None
    
    def _find_main_pyc(self, directory, exe_name):
        base = os.path.splitext(os.path.basename(exe_name))[0]
        for root, dirs, files in os.walk(directory):
            for f in files:
                if f.endswith('.pyc') and os.path.splitext(f)[0] == base:
                    return os.path.join(root, f)
        return None
    
    def _perform_extraction(self):
        if not self.file_path:
            self._log("请先选文件", "error")
            return
        
        final_dir = self._get_output_dir()
        if os.path.exists(final_dir):
            shutil.rmtree(final_dir)
        os.makedirs(final_dir, exist_ok=True)
        
        self._log("解包中...", "info")
        try:
            import pyinstxtractorcn
            pyinstxtractorcn.dcp(self.file_path, final_dir)
            self._log("✓ 解包完成", "success")
        except Exception as e:
            self._log(f"解包失败: {e}", "error")
            return
        
        main_pyc = self._find_main_pyc(final_dir, self.file_path)
        if not main_pyc:
            self._log("未找到主pyc", "warning")
            return
        
        self._log(f"找到: {os.path.basename(main_pyc)}", "info")
        
        success = False
        py_file = None
        used = None
        
        tools = self.tool_priority if self.auto_retry else [self.decompile_tool]
        for tool in tools:
            if not self.available_tools.get(tool, False):
                continue
            success, py_file = self._decompile_with_tool(main_pyc, tool)
            if success:
                used = tool
                break
        
        if success:
            self._log(f"✓ 成功! 工具: {used}", "success")
            if self.auto_fix and py_file:
                self._smart_fix_code(py_file)
            if used != self.decompile_tool:
                self.decompile_tool = used
        else:
            self._log("✗ 反编译失败", "error")

    def _fix_existing_file(self):
        """修复已有的py文件（支持目录浏览）"""
        print("\n" + "=" * 20)
        print("修复Python文件")
        print("=" * 20)

        # 先尝试找解包目录下的py文件
        final_dir = self._get_output_dir()
        py_files = []

        if final_dir and os.path.exists(final_dir):
            for root, dirs, files in os.walk(final_dir):
                for f in files:
                    if f.endswith('.py'):
                        py_files.append(os.path.join(root, f))

        if py_files:
            print("\n解包目录下的py文件:")
            for i, f in enumerate(py_files, 1):
                name = os.path.basename(f)
                size = os.path.getsize(f) / 1024
                print(f"{i}. {name} ({size:.1f}KB)")
            print(f"{len(py_files) + 1}. 浏览其他目录")
            print("0. 取消")

            ch = input(f"\n请选择 (1-{len(py_files) + 1}/0): ").strip()
            if ch == '0':
                return
            elif ch.isdigit():
                ch = int(ch)
                if 1 <= ch <= len(py_files):
                    self._smart_fix_code(py_files[ch - 1])
                    return
                elif ch == len(py_files) + 1:
                    self._browse_py_file()
                    return
                else:
                    self._log("无效选择", "error")
                    return
            else:
                self._log("无效输入", "error")
                return

        # 没有找到解包文件，直接浏览目录
        self._browse_py_file()

    def _browse_py_file(self):
        """浏览目录选择py文件"""
        current = os.getcwd()
        selected_file = None

        while True:
            print(f"\n当前目录: {current}")
            print("=" * 20)

            items = []
            items.append("..")  # 返回上级

            dirs = []
            files = []
            try:
                for f in os.listdir(current):
                    full = os.path.join(current, f)
                    if os.path.isdir(full):
                        dirs.append(f)
                    elif f.endswith('.py'):
                        size = os.path.getsize(full) / 1024
                        files.append(f"{f} ({size:.1f}KB)")
            except:
                pass

            dirs.sort()
            files.sort()

            for d in dirs:
                items.append(f"📁 {d}")
            for f in files:
                items.append(f"📄 {f}")

            for i, item in enumerate(items, 1):
                print(f"{i}. {item}")
            print("0. 返回")

            ch = input("\n请选择: ").strip()
            if ch == '0':
                break
            elif ch.isdigit():
                idx = int(ch) - 1
                if 0 <= idx < len(items):
                    selected = items[idx]
                    if selected == "..":
                        current = os.path.dirname(current)
                    elif selected.startswith("📁 "):
                        current = os.path.join(current, selected[2:])
                    elif selected.startswith("📄 "):
                        # 提取文件名（去掉大小信息）
                        fname = selected[2:].split(' (')[0]
                        selected_file = os.path.join(current, fname)
                        self._smart_fix_code(selected_file)
                        return
                else:
                    self._log("无效选择", "error")
            else:
                self._log("无效输入", "error")

        if not selected_file:
            self._log("未选择文件", "warning")

    
    def _compare_files(self):
        print("\n" + "=" * 20)
        print("代码对比")
        print("=" * 20)
        
        final_dir = self._get_output_dir()
        if not final_dir or not os.path.exists(final_dir):
            self._log("解包目录不存在，请先执行解包", "error")
            return
        
        dst_path = None
        exe_name = os.path.splitext(os.path.basename(self.file_path))[0] if self.file_path else ""
        
        for root, dirs, files in os.walk(final_dir):
            for f in files:
                if f.endswith('.py'):
                    if exe_name and os.path.splitext(f)[0] == exe_name:
                        dst_path = os.path.join(root, f)
                        break
                    if not dst_path:
                        dst_path = os.path.join(root, f)
            if dst_path:
                break
        
        if not dst_path:
            self._log("未找到反编译后的 .py 文件", "error")
            return
        
        dst_filename = os.path.basename(dst_path)
        dst_name = os.path.splitext(dst_filename)[0]
        self._log(f"反编译文件: {dst_filename}", "success")
        
        src_dir = os.getcwd()
        while True:
            print(f"\n当前目录: {src_dir}")
            print("0. 切换目录")
            print("直接回车使用当前目录")
            ch = input(": ").strip()
            if ch == '0':
                new_dir = input("请输入目录路径: ").strip().strip('"')
                if new_dir and os.path.exists(new_dir) and os.path.isdir(new_dir):
                    src_dir = new_dir
                    continue
                else:
                    self._log("目录不存在", "error")
                    continue
            else:
                break
        
        all_py_files = []
        for f in os.listdir(src_dir):
            if f.endswith('.py') and os.path.isfile(os.path.join(src_dir, f)):
                all_py_files.append(f)
        
        if not all_py_files:
            self._log(f"目录 {src_dir} 下没有 .py 文件", "error")
            return
        
        perfect_match = []
        partial_match = []
        for f in all_py_files:
            name = os.path.splitext(f)[0]
            if name == dst_name or f == dst_filename:
                perfect_match.append(f)
            elif dst_name in name or name in dst_name or (exe_name and exe_name in name):
                partial_match.append(f)
        
        matched = perfect_match + partial_match
        
        if not matched:
            self._log(f"未找到与 '{dst_name}' 相关的源文件", "warning")
            return
        
        print("\n" + "=" * 20)
        print("选择源文件")
        print("=" * 20)
        for i, f in enumerate(matched, 1):
            if f in perfect_match:
                print(f"{i}. ⭐ {f}")
            else:
                print(f"{i}.   {f}")
        
        if perfect_match:
            print("\n💡 ⭐ 为完全同名文件，推荐选择")
        
        ch2 = input("\n请选择: ").strip()
        if not ch2.isdigit() or not (1 <= int(ch2) <= len(matched)):
            self._log("无效选择", "error")
            return
        
        src_path = os.path.join(src_dir, matched[int(ch2)-1])
        self._log(f"源文件: {os.path.basename(src_path)}", "success")
        self._do_compare(src_path, dst_path)

    def _normalize_for_compare(self, text):
        """标准化文本用于比较（不改变原内容，只用于对比）"""

        # 使用正则匹配字符串内容，保持内容不变只改引号类型
        def replace_quotes(match):
            quote_char = match.group(1)
            content = match.group(2)
            # 统一转为单引号
            return f"'{content}'"

        # 匹配引号内的内容
        # 处理双引号字符串
        text = re.sub(r'"([^"\\]*(\\.[^"\\]*)*)"', replace_quotes, text)
        # 处理转义引号的情况
        return text

    def _do_compare(self, src, dst):
        """执行对比"""
        import difflib

        with open(src, 'r', encoding='utf-8') as f:
            src_content = f.read()
        with open(dst, 'r', encoding='utf-8') as f:
            dst_content = f.read()

        # 用于对比的标准化版本（不改变原始内容）
        src_norm = self._normalize_for_compare(src_content)
        dst_norm = self._normalize_for_compare(dst_content)

        # 提取函数
        def extract_funcs(content, original_content):
            funcs = {}
            lines = content.split('\n')
            orig_lines = original_content.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith('def '):
                    match = re.match(r'def\s+(\w+)\s*\(', line)
                    if match:
                        name = match.group(1)
                        # 保存标准化后的函数体
                        body = [lines[i]]
                        orig_body = [orig_lines[i]]
                        j = i + 1
                        indent = len(orig_lines[i]) - len(orig_lines[i].lstrip())
                        while j < len(lines):
                            if orig_lines[j].strip():
                                curr_indent = len(orig_lines[j]) - len(orig_lines[j].lstrip())
                                if curr_indent <= indent and orig_lines[j].strip().startswith('def '):
                                    break
                            body.append(lines[j])
                            orig_body.append(orig_lines[j])
                            j += 1
                        funcs[name] = {
                            'norm': '\n'.join(body),
                            'orig': '\n'.join(orig_body)
                        }
                        i = j - 1
                i += 1
            return funcs

        src_funcs = extract_funcs(src_norm, src_content)
        dst_funcs = extract_funcs(dst_norm, dst_content)

        src_names = set(src_funcs.keys())
        dst_names = set(dst_funcs.keys())

        print("\n" + "=" * 40)
        print("对比结果")
        print("=" * 40)
        print(f"源文件: {os.path.basename(src)}")
        print(f"反编译文件: {os.path.basename(dst)}")
        print(f"源函数数: {len(src_names)}")
        print(f"反编译函数数: {len(dst_names)}")

        # 同名函数
        common = src_names & dst_names
        only_src = src_names - dst_names
        only_dst = dst_names - src_names

        if common:
            print(f"\n✅ 同名函数: {len(common)} 个")

            # 对比函数体（使用标准化后的版本）
            identical = 0
            similar = 0
            diff = 0
            for name in common:
                if src_funcs[name]['norm'] == dst_funcs[name]['norm']:
                    identical += 1
                else:
                    ratio = difflib.SequenceMatcher(None, src_funcs[name]['norm'], dst_funcs[name]['norm']).ratio()
                    if ratio > 0.8:
                        similar += 1
                    else:
                        diff += 1

            print(f"\n📊 函数体对比（忽略引号差异）:")
            print(f"   完全相同: {identical}")
            print(f"   高度相似(>80%): {similar}")
            print(f"   差异较大: {diff}")

        if only_src:
            print(f"\n⚠️ 仅源文件有 ({len(only_src)}个):")
            for name in sorted(only_src)[:10]:
                print(f"   - {name}")

        if only_dst:
            print(f"\n⚠️ 仅反编译有 ({len(only_dst)}个):")
            for name in sorted(only_dst)[:10]:
                print(f"   - {name}")

        # 整体相似度
        total_ratio = difflib.SequenceMatcher(None, src_norm, dst_norm).ratio()
        print(f"\n📈 整体相似度: {total_ratio:.1%}")

        print("\n" + "=" * 40)
        if total_ratio > 0.85:
            print("✅ 反编译效果很好！")
        elif total_ratio > 0.6:
            print("⚠️ 反编译效果一般，存在差异")
        else:
            print("❌ 反编译效果较差，可能被混淆")
        print("=" * 40)

    def _clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def run(self):
        self._clear_screen()
        print("\n" + "*" * 40)
        print("          PyInstxtractorCN\n    (反编译pyinstaller打包的exe工具)")
        print("*" * 40)
        
        while True:
            available = self._get_available_names()
            #print("\n" + "=" * 20)
            print(f"[文件] {os.path.basename(self.file_path) if self.file_path else '无'}")
            print(f"[工具] {self.decompile_tool} ({available})")
            print(f"[轮换工具] {'开' if self.auto_retry else '关'}     [修复代码] {'开' if self.auto_fix else '关'}")
            print("")
            print("1.选择文件")
            print("2.输出目录")
            print("3.开始解包")
            print("4.选择工具")
            print("5.轮换(开/关)")
            print("6.修复(开/关)")
            print("7.修复文件")
            print("8.代码对比")
            print("9.清屏")
            print("0.退出")
            print("=" * 40)
            
            ch = input(": ").strip()
            if ch == '1':
                self._select_file()
            elif ch == '2':
                self._output_dir_setup()
            elif ch == '3':
                self._perform_extraction()
            elif ch == '4':
                self._select_tool()
            elif ch == '5':
                self.auto_retry = not self.auto_retry
                self._log(f"轮换工具: {'开' if self.auto_retry else '关'}", "success")
            elif ch == '6':
                self.auto_fix = not self.auto_fix
                self._log(f"修复代码: {'开' if self.auto_fix else '关'}", "success")
            elif ch == '7':
                self._fix_existing_file()
            elif ch == '8':
                self._compare_files()
            elif ch == '9':
                self._clear_screen()
            elif ch == '0' or ch == '' :
                self._log("再见！", "info")
                break

if __name__ == "__main__":
    try:
        PyInstxtractorCN_CLI().run()
    except KeyboardInterrupt:
        print("\n再见！")