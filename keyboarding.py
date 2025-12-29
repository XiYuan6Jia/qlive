import pygame
import keyboard
import threading
import time

class KeyboardListenerApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((600, 400))
        pygame.display.set_caption("Keyboard库演示")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # 键盘监听
        self.setup_global_listener()
        self.detected_keys = []
        
        # 字体 - 使用系统默认中文字体
        try:
            self.font = pygame.font.Font("C:/Windows/Fonts/simsun.ttc", 36)
        except:
            self.font = pygame.font.Font(None, 36)
    
    def setup_global_listener(self):
        """设置全局键盘监听"""
        def on_key_event(event):
            if event.event_type == keyboard.KEY_DOWN:
                key_name = event.name
                self.detected_keys.append(f"{key_name} (全局)")
                # 保持最近10个按键
                self.detected_keys = self.detected_keys[-10:]
                
                # 特殊按键处理
                if key_name == 'esc':
                    self.running = False
                elif key_name == 'space':
                    print("检测到全局空格键")
        
        # 注册全局监听
        keyboard.hook(on_key_event)
    
    def handle_events(self):
        """处理Pygame事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                # 本地按键（需要焦点）
                key_name = pygame.key.name(event.key)
                self.detected_keys.append(f"{key_name} (本地)")
                self.detected_keys = self.detected_keys[-10:]
    
    def draw(self):
        """绘制界面"""
        self.screen.fill((50, 50, 70))
        
        # 标题
        title = self.font.render("全局键盘监听演示", True, (0, 255, 255))
        self.screen.blit(title, (20, 20))
        
        # 检测到的按键
        keys_text = "最近按键:"
        keys_surface = self.font.render(keys_text, True, (255, 255, 255))
        self.screen.blit(keys_surface, (20, 80))
        
        for i, key_info in enumerate(self.detected_keys):
            color = (0, 255, 0) if "(全局)" in key_info else (255, 255, 0)
            key_surface = self.font.render(key_info, True, color)
            self.screen.blit(key_surface, (20, 120 + i * 30))
        
        # 说明
        info_text = [
            "红色: 需要窗口焦点",
            "绿色: 全局检测（无需焦点）",
            "按ESC退出"
        ]
        
        for i, line in enumerate(info_text):
            text = self.font.render(line, True, (200, 200, 200))
            self.screen.blit(text, (20, 300 + i * 30))
        
        pygame.display.flip()
    
    def run(self):
        """运行主循环"""
        try:
            while self.running:
                self.handle_events()
                self.draw()
                self.clock.tick(60)
        finally:
            keyboard.unhook_all()
            pygame.quit()

if __name__ == "__main__":
    app = KeyboardListenerApp()
    app.run()
