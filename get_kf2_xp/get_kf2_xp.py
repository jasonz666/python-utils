# encoding:utf-8

# 测试 pywin32 库的一些功能
# 使用 pywin32 刷 KF2 等级

import time
import win32gui, win32api, win32con

# KF2 客户端窗口的类名和标题
class_name = 'LaunchUnrealUWindowsClient'
title_name = 'Killing Floor 2 (64-bit, DX11) v1075'

hwnd = win32gui.FindWindow(class_name, title_name)
if hwnd == 0:
    print('KF2 Window not found.')
    exit(1)
print('KF2 hwnd:', hwnd)

left, top, right, bottom = win32gui.GetWindowRect(hwnd)
print('KF2 rect:', left, top, right, bottom)

win32gui.SetForegroundWindow(hwnd)
time.sleep(2)

count = 1
while True:
    curr_hwnd = win32gui.GetForegroundWindow()
    if  curr_hwnd == hwnd:
        win32api.keybd_event(71, 0, 0, 0)
        win32api.keybd_event(71, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.3)

        if count == 6:
            win32api.keybd_event(65, 0, 0, 0)
            time.sleep(0.2)
            win32api.keybd_event(65, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.1)

            win32api.keybd_event(68, 0, 0, 0)
            time.sleep(0.22)
            win32api.keybd_event(68, 0, win32con.KEYEVENTF_KEYUP, 0)

            count = 0

        count += 1
    else:
        time.sleep(2)
