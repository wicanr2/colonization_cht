#!/usr/bin/env python3
"""Docker/Xvfb 內向已完成走訪的自有視窗送正常關閉要求，讓前端保存收據。"""
import argparse
import ctypes as c
import os

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--window", type=lambda v: int(v, 0), required=True)
a = p.parse_args()
if not os.environ.get("DISPLAY") or a.window <= 0:
    raise ValueError("必須指定容器顯示器及有效視窗")


class Data(c.Union):
    _fields_ = [("b", c.c_char * 20), ("s", c.c_short * 10), ("l", c.c_long * 5)]


class Client(c.Structure):
    _fields_ = [("type", c.c_int), ("serial", c.c_ulong), ("send_event", c.c_int),
                ("display", c.c_void_p), ("window", c.c_ulong), ("message_type", c.c_ulong),
                ("format", c.c_int), ("data", Data)]


class Event(c.Union):
    _fields_ = [("client", Client), ("pad", c.c_long * 24)]


# 資料布局與 API 依既有驗證映像的 /usr/include/X11/Xlib.h；異平台拒絕。
if c.sizeof(c.c_long) != 8 or c.sizeof(Event) != 192 or c.sizeof(Client) != 96:
    raise ValueError("Xlib 資料布局不符")
x = c.CDLL("libX11.so.6")
x.XOpenDisplay.argtypes, x.XOpenDisplay.restype = [c.c_char_p], c.c_void_p
x.XInternAtom.argtypes, x.XInternAtom.restype = [c.c_void_p, c.c_char_p, c.c_int], c.c_ulong
x.XGetWMProtocols.argtypes = [c.c_void_p, c.c_ulong, c.POINTER(c.POINTER(c.c_ulong)), c.POINTER(c.c_int)]
x.XSendEvent.argtypes = [c.c_void_p, c.c_ulong, c.c_int, c.c_long, c.POINTER(Event)]
x.XFree.argtypes = [c.c_void_p]
x.XFlush.argtypes = x.XCloseDisplay.argtypes = [c.c_void_p]
d = x.XOpenDisplay(None)
if not d:
    raise ValueError("無法開啟容器顯示器")
try:
    close = x.XInternAtom(d, b"WM_DELETE_WINDOW", 1)
    protocol = x.XInternAtom(d, b"WM_PROTOCOLS", 1)
    protocols, count = c.POINTER(c.c_ulong)(), c.c_int()
    if not x.XGetWMProtocols(d, a.window, c.byref(protocols), c.byref(count)):
        raise ValueError("視窗未宣告正常關閉協定")
    try:
        if not close or not protocol or close not in [protocols[i] for i in range(count.value)]:
            raise ValueError("視窗不接受正常關閉要求")
    finally:
        x.XFree(protocols)
    event = Event()
    event.client.type, event.client.send_event = 33, 1  # Xlib ClientMessage
    event.client.display, event.client.window = d, a.window
    event.client.message_type, event.client.format = protocol, 32
    event.client.data.l[0] = close
    if not x.XSendEvent(d, a.window, 0, 0, c.byref(event)):
        raise ValueError("正常關閉要求未送達")
    x.XFlush(d)
finally:
    x.XCloseDisplay(d)
print("已送出正常關閉要求；仍須核對完整終點與輸入收據")
