import pyaudio
import numpy as np
import math
import time
import os

class AdvancedDBMonitor:
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.p = pyaudio.PyAudio()
        
        self.db_history = []
        self.max_history = 100
        
    def list_devices(self):
        """列出所有音频设备"""
        print("可用音频设备:")
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            if dev['maxInputChannels'] > 0:
                print(f"  {i}: {dev['name']} (输入通道: {dev['maxInputChannels']})")
    
    def start_monitoring(self, device_index=None):
        """开始监测"""
        try:
            stream = self.p.open(format=self.FORMAT,
                               channels=self.CHANNELS,
                               rate=self.RATE,
                               input=True,
                               input_device_index=device_index,
                               frames_per_buffer=self.CHUNK)
            
            print("开始监测麦克风分贝 (按Ctrl+C停止)")
            print("-" * 50)
            
            while True:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                
                # 计算分贝
                db = self.calculate_db(audio_data)
                self.db_history.append(db)
                if len(self.db_history) > self.max_history:
                    self.db_history.pop(0)
                
                # 显示信息
                self.display_info(db)
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\n监测结束")
        except Exception as e:
            print(f"错误: {e}")
        finally:
            if 'stream' in locals():
                stream.stop_stream()
                stream.close()
            self.p.terminate()
    
    def calculate_db(self, audio_data):
        """计算分贝值"""
        rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
        
        if rms > 0:
            db = 20 * math.log10(rms / 32768.0)
            db = max(0, db + 60)  # 调整到0-60范围
        else:
            db = 0
        
        return db
    
    def display_info(self, db):
        """显示分贝信息"""
        # 清屏
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # 分贝数值
        print(f"当前分贝: {db:5.1f} dB")
        
        # 音量条
        bar_length = 50
        filled = int(min(db / 60, 1.0) * bar_length)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"音量: |{bar}|")
        
        # 历史图表
        if self.db_history:
            chart_height = 10
            max_db = max(self.db_history) if max(self.db_history) > 0 else 60
            
            print("\n历史图表:")
            for level in range(chart_height, 0, -1):
                line = ""
                threshold = (level / chart_height) * max_db
                for hist_db in self.db_history[-50:]:  # 显示最近50个点
                    line += "█" if hist_db >= threshold else " "
                print(f"{level:2d}| {line}")
            
            print("   " + "‾" * 50)
        
        print("\n按 Ctrl+C 停止监测")

if __name__ == "__main__":
    monitor = AdvancedDBMonitor()
    monitor.list_devices()
    
    # 可以选择特定设备，不指定则使用默认设备
    device_index = None  # 或者指定设备索引
    
    monitor.start_monitoring(device_index)