import time
import os, sys 
import pyaudio
import time
import datetime
import struct
import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore

WIDTH = 2 # 信号值字节数
CHANNELS = 1 # 通道数
RATE = 44100 # 采样率
CHUNK = 128 # 批处理采样点数
FRAMES = 1000 # 每屏帧数
FREQ = 10 # 打印频率
FPS = 30 # 绘制帧率
LOUD = 10000 # 最大振幅

#----- 绘图处理

pg.setConfigOptions(antialias=True)

app = pg.mkQApp("Sound Dancer")

win = pg.GraphicsLayoutWidget(show=True, title="Sound Dancer")
win.resize(2000, 1200)
win.setWindowTitle('Sound Dancer')

signals = {
    1: []
    , 2: []
    , 4: []
    , 8: []
    , 16: []
    , 32: []
    , 64: []
    , 128: []
}
curves = {}
# signals

for i, k in enumerate(signals):
    plt = win.addPlot(title=f'Signals {k}'+(' FFT' if i%2==0 else ''))

    loud = LOUD * (1 if i%2==0 else 1)
    points = [loud*(i/FRAMES-0.5) for i in range(FRAMES)]

    if i%2==0:
        points=points[-100:]
        curves[k] = plt.plot(pen='y', stepMode="center", fillLevel=0, fillOutline=True, brush=(255,0,0,150))
        curves[k].setData(range(len(points)+1), points)
    else:
        curves[k] = plt.plot(pen='y')
        curves[k].setData(points)

    plt.enableAutoRange('xy', False)

    if i+1<len(signals) and i%2==1:
        win.nextRow()


ptr = 0
def update():
    global curve, curve2, ptr, signals

    for i, k in enumerate(signals):
        points = signals[k][-FRAMES:]
        if i%2==0:
            points=points[-100:]
            points = np.abs(np.fft.fftshift(np.fft.fft(points)))
            curves[k].setData(range(len(points)+1), points)
        else:
            curves[k].setData(points)
        if len(signals[k])%FRAMES == 0 and len(signals[k])/FRAMES > 2 :
            del signals[k][:-FRAMES]

    ptr += 1
    if ptr%FREQ==0:
        print('Update:', ptr)

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(1000 / FPS)

#----- 音频处理

pa = pyaudio.PyAudio()

idx=0

dt=np.dtype(np.int16)

def callback(in_data, frame_count, time_info, status):
    global idx, signals
    data = in_data
    sigarr = np.frombuffer(data, dt)

    signal = int(sigarr.mean())

    signals[1].extend(sigarr)

    sigarr = sigarr.reshape(-1, 2).mean(axis=-1)
    signals[2].extend(sigarr)

    sigarr = sigarr.reshape(-1, 2).mean(axis=-1)
    signals[4].extend(sigarr)

    sigarr = sigarr.reshape(-1, 2).mean(axis=-1)
    signals[8].extend(sigarr)

    sigarr = sigarr.reshape(-1, 2).mean(axis=-1)
    signals[16].extend(sigarr)

    sigarr = sigarr.reshape(-1, 2).mean(axis=-1)
    signals[32].extend(sigarr)

    sigarr = sigarr.reshape(-1, 2).mean(axis=-1)
    signals[64].extend(sigarr)

    sigarr = sigarr.mean()
    signals[128].append(sigarr)
    
    # print(f'In Data Len: {len(in_data)}, Frame: {frame_count}, Time: {datetime.datetime.fromtimestamp(time_info["current_time"])}, Status: {status}')
    if idx%FREQ==0:
        print(f'CHUNK[{idx}] = {data[0]:02X} {data[1]:02X} {data[2]:02X} ... {data[-3]:02X} {data[-2]:02X} {data[-1]:02X}, len={len(data)} {signal} {"|"*signal}')

    idx+=1
    # print(idx)
    return (in_data, pyaudio.paContinue)

if __name__ == '__main__':

    stream = pa.open(format=pa.get_format_from_width(WIDTH),
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    output=not True,
                    frames_per_buffer=CHUNK,
                    stream_callback=callback)

    stream.start_stream()

    pg.exec()

    while stream.is_active():
        time.sleep(0.1)

    stream.stop_stream()
    stream.close()

    pa.terminate()
