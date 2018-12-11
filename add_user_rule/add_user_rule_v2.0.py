# encoding:utf-8

## 添加用户自定义 pac 规则到 pac.txt 文件
## 自定义 pac 规则格式与 ss 的 user-rule.txt 一样
## 只要 v2rayN.exe 正在运行，脚本就能把 v2rayN.exe 所在目录
## 下的 user-rule.txt 自定义规则加入到 pac.txt 并重启 v2rayN.exe

import re
import psutil
import os
import time
import subprocess
from sys import platform

##-----------
## 变量定义
##-----------

v2n_name = 'v2rayN.exe'
chk_v2ctl = 'v2ctl.exe'
chk_v2ray = 'v2ray.exe'
chk_wv2ray = 'wv2ray.exe'
pac_file = 'pac.txt'
my_pac_file = 'user-rule.txt'

## 系统判断
if platform != 'win32':
    print('%s ERROR 000: only support Windows OS.' %
          time.strftime('[%Y-%m-%d_%H:%M:%S]'))
    exit(1)

##---------------
## 函数定义
##---------------

## 获取 v2rayN 进程列表
## 参数 pn 为进程名
## 返回 plist 为进程对象的列表
def getPlist(pn):
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

## 脚本不在 v2rayN 相同目录下
## 获取 v2rayN 所在目录
## 参数 pn 为进程名
## 参数 *sibling_files 为 v2ray 核心文件列表
## v2ray 核心文件有 v2ctl.exe 与 v2ray.exe 等
## 返回 v2_path 为 v2rayN 所在目录路径
## 返回 v2_pid 为 v2rayN 进程 pid
def getVPath_1(pn, *sibling_files):
    v2_path = ''
    ppath = []
    plist = getPlist(pn)

    ## 没有找到进程就退出
    if not plist:
        print('%s ERROR 001: %s: process not found.' % (
            time.strftime('[%Y-%m-%d_%H:%M:%S]'), pn))
        exit(1)

    ## 获取进程所在绝对路径
    try:
        for path in plist:
            ppath.append((path.exe(), path.pid))
    except psutil.NoSuchProcess:
        pass

    ## 检查 v2rayN 文件是否存在
    if not ppath:
        print('%s ERROR 002: %s: can not get process abs path.' % (
            time.strftime('[%Y-%m-%d_%H:%M:%S]'), pn))
        exit(1)

    ## 检查 v2rayN 防止进程同名
    sibling_count = 0
    v2_pid = 0
    for name in ppath:
        if not os.path.isfile(name[0]):
            print('%s ERROR 003: %s: file not found.' % (
                time.strftime('[%Y-%m-%d_%H:%M:%S]'), pn))
            exit(1)
        v2_path = os.path.dirname(name[0])
        for fn in sibling_files:
            ## v2rayN 通常会与 v2ray.exe 等核心文件在同目录下
            ## 如果不在同目录下就退出脚本，防止同名 v2rayN.exe 进程
            if not os.path.isfile(v2_path + os.sep + fn):
                print('%s ERROR 004: this is not real %s.' % (
                    time.strftime('[%Y-%m-%d_%H:%M:%S]'), pn))
                exit(1)
            else:
                sibling_count += 1
        ## 如果核心文件与 v2rayN 都在一起了就退出迭代
        ## 防止有同名进程执行多余的迭代循环造成脚本退出
        if sibling_count == len(sibling_files ):
            v2_pid = name[1]
            break
    return v2_path, v2_pid

## 检查默认 pac 文件是否存在
## 参数 vp 为 v2rayN.exe 所在路径
## 参数 pac_fn 为 pac 文件名
## 返回 pac 文件绝对路径
def chkPacExist(vp, pac_fn):
    if not os.path.isfile(vp + os.sep + pac_fn):
        print('%s ERROR 005: %s: pac file not found.' % (
            time.strftime('[%Y-%m-%d_%H:%M:%S]'), pac_fn))
        exit(1)
    return vp + os.sep + pac_fn

##----------
## main
##----------

## 获取 v2rayN.exe 文件所在路径
v2n_path, v_pid = getVPath_1(v2n_name, chk_wv2ray, chk_v2ctl, chk_v2ray)

## 检查 pac 文件存在否
pac_path = chkPacExist(v2n_path, pac_file)

## 检查自定义 pac 文件存在否
my_pac_path = v2n_path + os.sep + my_pac_file
if not os.path.isfile(my_pac_path):
    if not os.access(v2n_path, os.W_OK):
        print('%s ERROR 006: %s: can not write file.' % (
            time.strftime('[%Y-%m-%d_%H:%M:%S]'), v2n_path))
        exit(1)
    with open(my_pac_path, 'w', encoding='UTF-8') as fd:
        fd.write('! Put user rules line by line in this file.\n')
        fd.write('! See https://adblockplus.org/en/filter-cheatsheet\n')
        print('%s INFO: %s: new file created.' %
              (time.strftime('[%Y-%m-%d_%H:%M:%S]'), my_pac_file))

exp = re.compile(r'"(.*?)"')
exp2 = re.compile(r'",')

## 开始处理 pac 规则
print('%s INFO: start to add user pac rules ...' %
      time.strftime('[%Y-%m-%d_%H:%M:%S]'))

## 读取自定义 pac 文件
print('%s INFO: reading %s file ...' %
      (time.strftime('[%Y-%m-%d_%H:%M:%S]'), my_pac_file))
user_pac = []
with open(my_pac_path, 'r', encoding='UTF-8') as fd:
    for line in fd:
        if not line.startswith('!'):
            user_pac.append(line)

## 处理自定义规则
user_pac = [pac.strip('"\',\n') for pac in user_pac]

## 读取默认 pac 文件
print('%s INFO: reading %s file ...' %
      (time.strftime('[%Y-%m-%d_%H:%M:%S]'), pac_file))
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

## 处理默认规则
default_pac = [exp.findall(pac)[0] for pac in default_pac]

## 冲突检查
## 检查自定义规则是否已经在默认规则中排除
print('%s INFO: checking conflict rules ...' %
      time.strftime('[%Y-%m-%d_%H:%M:%S]'))
for pac in user_pac:
    if not pac.startswith('@@'):
        if '@@' + pac in default_pac:
            print('%s WARNING: %s: user rule exclude item exist in %s.' % (
                time.strftime('[%Y-%m-%d_%H:%M:%S]'), pac, pac_file))
            default_pac.remove('@@' + pac)
            print('%s WARNING: %s: conflict item removed from %s.' % (
                time.strftime('[%Y-%m-%d_%H:%M:%S]'), '@@' + pac, pac_file))

## 合并 pac 规则
print('%s INFO: add user rules %d lines.' % (
    time.strftime('[%Y-%m-%d_%H:%M:%S]'), len(user_pac)))

new_pac = user_pac + default_pac
new_pac = ['  "' + pac.strip() + '",\n' for pac in new_pac]
new_pac[-1] = exp2.sub('"', new_pac[-1])

## 保存 pac 文件
with open(pac_path, 'rb') as fd:
    ## 先备份默认 pac 文件
    with open(pac_path + '.bak', 'wb') as bak_fd:
        bak_fd.write(fd.read())

print('%s INFO: save user rules to %s file ...' % (
    time.strftime('[%Y-%m-%d_%H:%M:%S]'), pac_file))
with open(pac_path, 'w', encoding='UTF-8') as fd:
    for line in pac_file_line:
        if not line.startswith('var rules = ['):
            fd.write(line)
        else:
            fd.write(line)
            fd.writelines(new_pac)

## 重启 v2rayN.exe 进程
print('%s INFO: restart %s ...' %
      (time.strftime('[%Y-%m-%d_%H:%M:%S]'), v2n_name))

if v_pid > 0:
    p = psutil.Process(v_pid)
    p.kill()
    time.sleep(1)

## 创建一个子进程对象
## 如果脚本意外退出，子进程也会跟着退出
child = subprocess.Popen(v2n_path + os.sep + v2n_name)
time.sleep(1)
print('%s INFO: ALL DONE.' % time.strftime('[%Y-%m-%d_%H:%M:%S]'))
print('%s INFO: Press Enter to Exit.' % time.strftime('[%Y-%m-%d_%H:%M:%S]'))
input()
