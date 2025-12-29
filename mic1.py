import pyaudio
import numpy as np
import math
import time

def pyaudio_db_detection():
    """使用pyaudio进行分贝检测"""
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    
    p = pyaudio.PyAudio()
    
    print("可用输入设备:")
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            print(f"  {i}: {dev['name']}")
    
    try:
        # 打开麦克风流
        stream = p.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       input=True,
                       frames_per_buffer=CHUNK)
        
        print("开始监测麦克风分贝 (按Ctrl+C停止)")
        print("-" * 40)
        
        while True:
            # 读取音频数据
            data = stream.read(CHUNK, exception_on_overflow=False)
            
            # 转换为numpy数组
            audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            
            # 计算RMS
            rms = np.sqrt(np.mean(audio_data ** 2))
            
            # 计算分贝
            if rms > 0:
                db = 20 * math.log10(rms / 32768.0)  # 16位音频参考
                db = max(0, db + 60)  # 调整到合理范围
            else:
                db = 0
            
            # 创建音量条
            bar_length = 50
            filled = int(min(db / 60, 1.0) * bar_length)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            print(f"分贝: {db:5.1f} dB |{bar}|", end='\r')
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n监测结束")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    pyaudio_db_detection()