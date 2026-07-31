import os
import pygame
import array

# 初始化Pygame并设置窗口大小
pygame.init()
size = width, height = (800, 600)
screen = pygame.display.set_mode(size)

# 对于Windows系统
if os.name == 'nt':
    import win32gui, win32con
    hwnd = pygame.display.get_wm_info()['window']
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
elif os.name == 'posix': 
    # 对于Linux/MacOSX系统（部分桌面环境支持）
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk, GdkX11, Gdk, GdkGravity
        
        def on_window_mapped(widget):
            display = GdkX11.X11Display.get_default()
            xdisplay = GdkX11.x11_get_x_display()
            xid = widget.get_window().get_xid()
            leader = None

            prop = display.property_get(display.get_default_screen().get_root_window(), "WM_CLIENT_LEADER", "WINDOW")
            if len(prop.value) > 0:
                leader = prop.value[0]

            hints = [GdkGravity.NORTH_WEST,
                     GdkGravity.NORTH_WEST,
                     0, 0,
                     Gdk.WindowHints.STICKY |
                     Gdk.WindowHints.URGENCY]

            display.change_property(xdisplay.root, "_NET_WM_STATE",
                                   "ATOM", 32,
                                   Gdk.PropMode.REPLACE,
                                   [display.intern_atom("_NET_WM_STATE_STAYS_ON_TOP"),
                                    display.intern_atom("_NET_STARTUP_ID")])

            if leader != None and leader != xid:
                atom_net_client_list = display.intern_atom("_NET_CLIENT_LIST_STACKING")
                client_list = display.property_get(atom_net_client_list, "WINDOW")[2]
                new_client_list = []
                for w in reversed(client_list):
                    if w != xid:
                        new_client_list.append(w)
                    else:
                        break

                new_client_list.insert(0,xid)
                display.change_property(root, atom_net_client_list,
                                       "WINDOW", 32,
                                       Gdk.PropMode.REPLACE,
                                       array.array('I',new_client_list))

        window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        window.connect("map-event", lambda wid,e:on_window_mapped(window))
        window.fullscreen()
    except Exception as e:
        print(f"无法启用顶层窗口特性: {str(e)}")
pygame.display.set_caption("Always On Top Window Example")
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    screen.fill((0, 0, 0))  # 填充背景色为黑色
    pygame.display.flip()   # 更新整个待显示的 Surface 对象到屏幕上
pygame.quit()