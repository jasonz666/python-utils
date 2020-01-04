#!/usr/bin/env python
# encoding:utf-8
# file: add_user_rule.py

# 添加用户自定义 pac 规则到 pac.txt 文件
# 自定义 pac 规则格式与 ss 的 user-rule.txt 一样
# 只要 v2rayN.exe 正在运行，就能把 v2rayN.exe 所在目录
# 下的 user-rule.txt 自定义规则加入到 pac.txt 并重启 v2rayN.exe

# TODO 未实现功能
# 无法判断 user-rule.txt 中url规则完全一样的项
# 不会检查 user-rule.txt 中既存在规则又排除规则的同一个url冲突项

import re
import psutil
import os
import time
import subprocess
import chardet
from sys import platform


# 获取 v2rayN 进程列表
# 参数 pn 为进程名
# 返回 plist 为进程对象的列表
def get_plist(pn):
    plist = []
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=['name', 'pid'])
        except psutil.NoSuchProcess:
            pass
        else:
            if pinfo['name'] == pn:
                plist.append(psutil.Process(pinfo['pid']))
    return plist


# 获取 v2rayN 所在目录
# 参数 pn 为进程名
# 参数 *sibling_files 为 v2ray 核心文件列表
# v2ray 核心文件有 v2ctl.exe 与 v2ray.exe 等
# 返回 v2_path 为 v2rayN 所在目录路径
# 返回 v2_pid 为 v2rayN 进程 pid
def get_vpath_1(pn, *sibling_files):
    v2_path = ''
    ppath = []
    plist = get_plist(pn)

    # 没有找到进程就退出
    if not plist:
        print('%s ERROR: %s: process not found.' % (nowtime(), pn))
        exit(1)

    # 获取进程所在绝对路径
    try:
        for path in plist:
            ppath.append((path.exe(), path.pid))
    except psutil.NoSuchProcess:
        pass

    # 检查 v2rayN 文件是否存在
    if not ppath:
        print('%s ERROR: %s: can not get process abs path.' % (nowtime(), pn))
        exit(1)

    # 检查 v2rayN 防止进程同名
    sibling_count = 0
    v2_pid = 0
    for name in ppath:
        if not os.path.isfile(name[0]):
            print('%s ERROR: %s: file not found.' % (nowtime(), pn))
            exit(1)
        v2_path = os.path.dirname(name[0])
        for fn in sibling_files:
            # v2rayN 通常会与 v2ray.exe 等核心文件在同目录下
            # 如果不在同目录下就退出脚本，防止同名 v2rayN.exe 进程
            if not os.path.isfile(v2_path + os.sep + fn):
                print('%s ERROR: this is not real %s.' % (nowtime(), pn))
                exit(1)
            else:
                sibling_count += 1
        # 如果核心文件与 v2rayN 都在一起了就退出迭代
        # 防止有同名进程执行多余的迭代循环造成脚本退出
        if sibling_count == len(sibling_files):
            v2_pid = name[1]
            break
    return v2_path, v2_pid


# 检查默认 pac 文件是否存在
# 参数 vp 为 v2rayN.exe 所在路径
# 参数 pac_fn 为 pac 文件名
# 返回 pac 文件绝对路径
def chk_pac_exist(vp, pac_fn):
    if not os.path.isfile(vp + os.sep + pac_fn):
        print('%s ERROR: %s: pac file not found.' % (nowtime(), pac_fn))
        exit(1)
    return vp + os.sep + pac_fn


# 检查自定义 pac 文件存在否
# 参数 vp 为 v2rayN.exe 所在路径
# 参数 my_pac_fn 为自定义 pac 文件名
# 不存在则创建自定义 pac 文件
def chk_mypac_exist(vp, my_pac_fn):
    abs_path = vp + os.sep + my_pac_fn
    if not os.path.isfile(abs_path):
        if not os.access(vp, os.W_OK):
            print('%s ERROR: %s: can not write file.' % (nowtime(), vp))
            exit(1)
        with open(abs_path, 'w', encoding='UTF-8') as fd_pac:
            fd_pac.write('! Put user rules line by line in this file.\n')
            fd_pac.write('! See https://adblockplus.org/en/filter-cheatsheet\n')
            print('%s INFO: %s: new file created.' % (nowtime(), my_pac_fn))


# 当前时间 输出信息前缀
def nowtime():
    return time.strftime('[%Y-%m-%d %H:%M:%S]')


# ###########
# 主程序
# ###########

v2n_name = 'v2rayN.exe'
chk_v2ctl = 'v2ctl.exe'
chk_v2ray = 'v2ray.exe'
chk_wv2ray = 'wv2ray.exe'
pac_file = 'pac.txt'
my_pac_file = 'user-rule.txt'
editor = 'notepad.exe'

# 系统判断
if platform != 'win32':
    print('%s ERROR: only support Windows OS.' % nowtime())
    exit(1)

# 获取 v2rayN.exe 文件所在路径
v2n_path, v_pid = get_vpath_1(v2n_name, chk_wv2ray, chk_v2ctl, chk_v2ray)

# 检查 pac 文件存在否
pac_path = chk_pac_exist(v2n_path, pac_file)

# 检查自定义 pac 文件存在否
chk_mypac_exist(v2n_path, my_pac_file)

# 用指定的文本编辑器打开自定义 pac 文件
my_pac_path = v2n_path + os.sep + my_pac_file

print('%s INFO: opening %s with %s editor ...' % (nowtime(), my_pac_file, editor))
print('%s INFO: --> ADD YOUR OWN RULE LINE BY LINE IN %s FILE.' % (nowtime(), my_pac_file))
print('%s INFO: --> WHEN YOU ADD RULE COMPLETE OR ADD NOTHING,' % nowtime())
print('%s INFO: --> SAVE IT THEN CLOSE %s EDITOR.' % (nowtime(), editor))
print('%s INFO: waiting until %s exit ...' % (nowtime(), editor))
os.system('%s %s' % (editor, my_pac_path))

# 开始处理 pac 规则
print('%s INFO: start to add user pac rules ...' % nowtime())

exp = re.compile(r'"(.*?)"')
exp2 = re.compile(r'",')

# 检测默认 pac 和自定义 pac 文件是否为可识别编码
with open(my_pac_path, 'rb') as fd:
    data = fd.read()
    result = chardet.detect(data)
    ret_encode = result['encoding'].lower()
    if ret_encode not in ['utf-8-sig', 'ascii', 'utf-8']:
        print('%s ERROR: %s: is %s encoding (only support ascii, uft-8, UTF-8-BOM).' % (
            nowtime(), my_pac_path, result['encoding']))
        exit(1)
with open(pac_path, 'rb') as fd:
    data = fd.read()
    result = chardet.detect(data)
    ret_encode = result['encoding'].lower()
    if ret_encode not in ['utf-8-sig', 'ascii', 'utf-8']:
        print('%s ERROR: %s: is %s encoding (only support ascii, uft-8, UTF-8-BOM).' % (
            nowtime(), pac_path, result['encoding']))
        exit(1)

# 读取自定义 pac 文件
print('%s INFO: reading %s file ...' % (nowtime(), my_pac_file))

user_pac = []
with open(my_pac_path, 'r', encoding='UTF-8') as fd:
    for line in fd:
        if not line.startswith('!'):
            user_pac.append(line)

# 处理自定义规则
user_pac = [pac.strip('"\',\n') for pac in user_pac]
user_pac_rules = len(user_pac)

# 读取默认 pac 文件
print('%s INFO: reading %s file ...' % (nowtime(), pac_file))

default_pac = []
pac_file_line = []
with open(pac_path, 'r', encoding='UTF-8') as fd:
    for line in fd:
        if not line.startswith('var rules = ['):
            pac_file_line.append(line)
        else:
            pac_file_line.append(line)
            for line1 in fd:
                if not line1.startswith('];'):
                    default_pac.append(line1)
                else:
                    pac_file_line.append(line1)
                    break

# 处理默认规则
default_pac = [exp.findall(pac)[0] for pac in default_pac]

# 冲突检查
# 检查自定义规则是否已经在默认规则中排除
print('%s INFO: checking conflict rules ...' % nowtime())

remove_rules = 0
for pac in user_pac:
    if not pac.startswith('@@'):
        if '@@' + pac in default_pac:
            print('%s WARNING: %s: user rule exclude item exist in %s.' % (nowtime(), pac, pac_file))
            default_pac.remove('@@' + pac)
            remove_rules += 1
            print('%s WARNING: %s: conflict item removed from %s.' % (nowtime(), '@@' + pac, pac_file))

# 合并 pac 规则
# 排除user_pac中的项在default_pac中已存在的项 这样就能重复执行脚本
dft_pac = set(default_pac)
tmp_pac = []
exist_rules = 0
for i in user_pac:
    if i not in dft_pac:
        tmp_pac.append(i)
    else:
        exist_rules += 1
        print('%s WARNING: rule exist in %s: %s' % (nowtime(), pac_file, i))
user_pac = tmp_pac
new_pac = user_pac + default_pac
new_pac = ['  "' + pac.strip() + '",\n' for pac in new_pac]
new_pac[-1] = exp2.sub('"', new_pac[-1])

# 保存 pac 文件
with open(pac_path, 'rb') as fd:
    # 先备份默认 pac 文件
    with open(pac_path + '.bak', 'wb') as bak_fd:
        bak_fd.write(fd.read())

print('%s INFO: save user rules to %s file ...' % (nowtime(), pac_file))

with open(pac_path, 'w', encoding='UTF-8') as fd:
    for line in pac_file_line:
        if not line.startswith('var rules = ['):
            fd.write(line)
        else:
            fd.write(line)
            fd.writelines(new_pac)

# 重启 v2rayN.exe 进程
print('%s INFO: restart %s ...' % (nowtime(), v2n_name))

if v_pid > 0:
    p = psutil.Process(v_pid)
    p.kill()
    time.sleep(1)

# 创建一个子进程对象
# 如果脚本意外退出，子进程也会跟着退出
child = subprocess.Popen(v2n_path + os.sep + v2n_name)
time.sleep(1)
print('%s INFO: total %d rules in %s, add %d rules to %s' % (
    nowtime(), user_pac_rules, my_pac_file, user_pac_rules - exist_rules - remove_rules, pac_file))
print('%s INFO: ALL DONE.' % nowtime())
input('%s INFO: Press Enter to Exit. ' % nowtime())
