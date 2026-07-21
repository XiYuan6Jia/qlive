import pygame as pg
from gif_to_frames import extract_frames as read_gif
import queue, threading, os, math,socket,json,time
import pyaudio
import numpy as np
import keyboard

class gif:
    def __init__(self, path, scale=1, speed=1, start_frame=1):
        self.frames = read_gif(path,start_frame)
        self.scale = scale
        self.current_frame = 0
        self.current_frame_time = 0.0
        self.total_frames = len(self.frames)
        self.image_surfaces = [self.pil_to_surface(frame) for frame in self.frames]
        self.speed = speed

    def pil_to_surface(self, pil_image):
        """Convert a PIL Image to a Pygame Surface."""
        mode = pil_image.mode
        size = pil_image.size
        data = pil_image.tobytes()

        if mode == "RGBA":
            surface = pg.image.fromstring(data, size, mode).convert_alpha()
        else:
            surface = pg.image.fromstring(data, size, mode).convert()

        if self.scale != 1:
            new_size = (int(size[0] * self.scale), int(size[1] * self.scale))
            surface = pg.transform.scale(surface, new_size)

        return surface

    def get_frame(self):
        """Get the current frame as a Pygame Surface."""
        frame_surface = self.image_surfaces[self.current_frame]
        self.current_frame_time = (self.current_frame_time + self.speed) % self.total_frames
        self.current_frame = int(round(self.current_frame_time)) % self.total_frames
        return frame_surface
    
class listener:
    def __init__(self,host='localhost', port=9999):
        self.host = host
        self.port = port
        self.welcome_msg = ""
        self.trigger_animation = 'NONE'
        self.triggered = False
    
    def start_server(self):
        self.observer_thread = threading.Thread(target=self._observing, daemon=True)
        self.observer_thread.start()

    def _observing(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"监听服务器已启动，等待连接 {self.host}:{self.port} ...")

        while True:
            try:
                conn, addr = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(conn, addr),
                    daemon=True
                )
                client_thread.start()
            except socket.timeout:
                continue
            except OSError:
                break

        pass

    def handle_client(self, conn, addr):
        try:
            data = conn.recv(1024)
            if data:
                vote_data = json.loads(data.decode('utf-8'))
                self._process(vote_data)
        except Exception as e:
            print(f"处理弹幕数据错误: {e}")
        finally:
            conn.close()

    def _stop_thread(self,stoptime=3):
        time.sleep(stoptime)
        self.trigger_animation = 'NONE'
        self.triggered = False

    def _process(self, data):
        cmd = data.get('cmd', '')
        if cmd == 'INTERACT_WORD_V2':
            self.welcome_msg = data.get('msg', '')
            print(self.welcome_msg)
        if cmd == 'DANMU_MSG':
            msg = data.get('msg', '')
            uname = data.get('uname', '')
            print(f"{uname} 说: {msg}")
            if "哈气" in msg:
                self.trigger_animation = 'haqi'
                self.triggered = True
                stop_thread = threading.Thread(target=self._stop_thread, args=(1,), daemon=True)
                stop_thread.start()
            if "摸头" in msg:
                self.trigger_animation = 'motou'
                self.triggered = True
                stop_thread = threading.Thread(target=self._stop_thread, args=(1,), daemon=True)
                stop_thread.start()

class qlive:
    def __init__(self,width=800, height=600):
        pg.init()
        self.screen = pg.display.set_mode((width, height))
        pg.display.set_caption("Qlive")
        self.clock = pg.time.Clock()
        self.running = True
        self.fps = 30
        self.db_queue = queue.Queue()
        self.is_db_monitoring = True
        self.srart_db_monitoring()
        self.force_play = False
        self.pressed_keys = set()
        self.setup_global_listener()
        self.oserver = listener()
        self.triggered = False
        self.stoptime = 0
        self.oserver.start_server()
        self.layer_2 = None

    def check_trigger(self):
        if not self.triggered:
            animation = self.oserver.trigger_animation
            self.triggered = self.oserver.triggered
            if animation == 'haqi':
                self.layer_1 = self.gif2
                self.stoptime = pg.time.get_ticks() + 5000
            elif animation == 'motou':
                self.layer_1 = self.gif1
                self.layer_2 = self.gif_handslap
                self.stoptime = pg.time.get_ticks() + 4000
        if self.triggered and pg.time.get_ticks() > self.stoptime:
            self.layer_1 = self.gif0
            self.layer_2 = None
            self.triggered = False
            self.oserver.trigger_animation = 'NONE'

    def setup_global_listener(self):
        def on_pressed(event):
            
            pass
        pass
        
        def on_released(event):
            
            pass

        def on_shortcut_default():
            self.layer_1 = self.gif0
            self.force_play = False
            self.triggered = False

        def on_shortcut_gif1():
            self.layer_1 = self.gif1
            self.force_play = True
            self.triggered = False

        def on_shortcut_gif2():
            self.layer_1 = self.gif2
            self.force_play = True
            self.triggered = False

        keyboard.add_hotkey('ctrl+1', on_shortcut_default)
        keyboard.add_hotkey('ctrl+2', on_shortcut_gif1)
        keyboard.add_hotkey('ctrl+3', on_shortcut_gif2)
        keyboard.on_press(on_pressed)
        keyboard.on_release(on_released)

    def srart_db_monitoring(self):
        if self.is_db_monitoring:
            db_thread = threading.Thread(target=self.db_monitor, daemon=True)
            db_thread.start()

    def db_monitor(self):
        """使用pyaudio进行分贝检测并将结果放入队列"""
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        
        p = pyaudio.PyAudio()
        
        try:
            stream = p.open(format=FORMAT,
                           channels=CHANNELS,
                           rate=RATE,
                           input=True,
                           frames_per_buffer=CHUNK)
            
            while True:
                data = stream.read(CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                
                rms = np.sqrt(np.mean(audio_data ** 2))
                
                if rms > 0:
                    db = 20 * math.log10(rms / 32768.0)
                    db = max(0, db + 60)
                else:
                    db = 0
                
                self.db_queue.put(db)
                pg.time.wait(100)
                
        except Exception as e:
            print(f"DB监测错误: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

    def load_gif(self):
        # Use forward slashes to avoid escape-sequence warnings on Windows
        self.gif0 = gif("animations/default.gif", scale=1)
        self.gif1 = gif("animations/wizzle2.gif", scale=1,speed=0.75)
        self.gif2 = gif("animations/shoot.gif", scale=1,speed=0.75)
        self.gif_speak = gif("animations/speak.gif", scale=1,speed=1.25)
        self.gif_handslap = gif("animations/handslap.gif", scale=1,speed=1)

        self.layer_1 = self.gif0

    def display_gif(self, gifx: gif, x=0, y=0):
        frame = gifx.get_frame()
        self.screen.blit(frame, (x, y))

    def run(self):
        while self.running:
            self.check_trigger()
            #麦克风
            if self.is_db_monitoring and not self.db_queue.empty():
                db_value = self.db_queue.get()
                if self.triggered == False:
                    if db_value < 15 and not self.force_play:
                        self.layer_1 = self.gif0
                    elif not self.force_play:
                        self.layer_1 = self.gif_speak

            #键盘事件
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False


            self.screen.fill((0, 255, 0))

            #图层1
            self.display_gif(self.layer_1)
            #图层2
            if self.layer_2:
                self.display_gif(self.layer_2)

            pg.display.flip()
            self.clock.tick(self.fps)

        pg.quit()

if __name__ == "__main__":
    app = qlive()
    app.load_gif()
    app.run()