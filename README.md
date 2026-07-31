# qlive — 弹幕驱动的桌面虚拟形象 / 动画播放器

一个面向直播互动的桌面虚拟形象播放器。支持**透明无边框置顶窗口**、**麦克风音量驱动动画**、**B站弹幕/事件触发动作**，可用作 OBS 直播挂件或桌面宠物。

## ✨ 核心特性

- 🖥️ **桌面置顶透明窗口** — 无边框、品红色色键抠像、始终置顶、可拖拽移动（`qlive_desktop.py`）
- 🎤 **麦克风音量驱动** — 实时检测分贝值，说话时自动切换到"讲话"动画，静音时切回默认待机
- 💬 **B站直播弹幕联动** — 接收弹幕消息，关键词映射到指定动画（如"摸头"→摸头动画、"哈气"→射击动画）
- 🎬 **GIF 逐帧播放** — 支持 GIF 动画资源，可调节播放速度和缩放
- ⌨️ **键盘快捷键** — `Ctrl+0/1/2` 手动切换动画，ESC 退出
- 🖱️ **右键菜单** — 内置退出选项
- 🔧 **模块化设计** — 弹幕接收、音频检测、动画播放各自独立，易于扩展

## 📁 项目结构

| 文件 | 说明 |
|------|------|
| `qlive_desktop.py` | ⭐ **主程序** — 桌面透明置顶虚拟形象（推荐使用） |
| `qlive2.py` | 增强版 — 含 TCP 服务端接收弹幕事件，支持弹幕关键词触发动画 |
| `qlive.py` | 基础版 — 普通窗口模式，麦克风 + 键盘控制动画 |
| `get_danmu.py` | B站直播间弹幕监听，通过 `client.py` 转发到 `qlive2.py` |
| `client.py` | TCP 客户端，将弹幕数据 JSON 序列化后发送到服务端 |
| `gif_to_frames.py` | 工具：将 GIF 拆解为 PIL Image 帧列表 |
| `keyboarding.py` | 键盘监听演示（全局热键 + Pygame 本地按键） |
| `mic1.py` | 麦克风分贝检测演示（命令行实时显示） |
| `mic2.py` | 高级麦克风监测演示（含历史图表） |
| `exampleoftopmost.py` | 窗口置顶技术验证（pywin32） |
| `animations/` | 动画资源目录，放置 `.gif` 文件 |
| `credential.json` | B站 API 凭证（需自行创建，已 .gitignore） |

## 🚀 快速开始（Windows）

### 1. 创建虚拟环境并安装依赖

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install pygame pyaudio numpy pillow pywin32 keyboard bilibili-api
```

### 2. 运行桌面虚拟形象（推荐）

```powershell
.\.venv\Scripts\Activate.ps1
python qlive_desktop.py
```

窗口将出现在屏幕右下角，品红色背景在 OBS 中可通过色键抠除。

### 3. （可选）联动 B 站弹幕

1. 创建 `credential.json`（B站 API 凭证，参考下方配置）
2. 先启动 `qlive2.py`（内置 TCP 服务端，监听 `localhost:9999`）
3. 再运行 `get_danmu.py`（连接 B 站直播间，弹幕转发到 qlive2）

```powershell
# 终端 1
python qlive2.py

# 终端 2
python get_danmu.py
```

## ⚙️ 配置

`credential.json` 示例（B站 Credential）：

```json
{
  "dedeuserid": "",
  "sessdata": "",
  "bili_jct": "",
  "buvid3": "",
  "ac_time_value": ""
}
```

> ⚠️ **安全提示**：该文件已加入 `.gitignore`，请勿将真实凭证提交到公共仓库。

## 🎮 操作说明

| 操作 | 效果 |
|------|------|
| 麦克风说话 | 自动切到"讲话"动画 |
| 静音 | 自动切回"待机"动画 |
| `Ctrl+0` | 强制切回默认待机动画 |
| `Ctrl+1` | 强制播放动画1 (wizzle2) |
| `Ctrl+2` | 强制播放动画2 (shoot) |
| 鼠标左键拖拽 | 移动窗口位置 |
| 鼠标右键 | 弹出菜单（退出） |
| `ESC` | 退出程序 |

## 🎨 自定义动画

在 `animations/` 目录下放置 GIF 文件，然后在 `qlive_desktop.py` 的 `load_gif()` 方法中注册：

```python
self.gif_custom = gif("animations/你的动画.gif", scale=1, speed=1.0)
```

### 弹幕关键词 → 动画映射

在 `qlive2.py` 的 `listener._process()` 中添加规则：

```python
if "关键词" in msg:
    self.trigger_animation = 'custom'
    self.triggered = True
```

## 📦 依赖

- **pygame** — 图形渲染与窗口管理
- **pyaudio** — 麦克风音频采集
- **numpy** — 音频数据处理
- **Pillow** — GIF 帧解析
- **pywin32** — Windows 窗口置顶/透明/色键
- **keyboard** — 全局热键
- **bilibili-api** — B站直播弹幕 API（可选）

## 🔮 扩展方向

- [ ] 集成 TTS 语音合成回应弹幕
- [ ] 支持更多动画图层叠加
- [ ] GUI 设置面板（热键配置、动画映射）
- [ ] OSC/WebSocket 通知输出
- [ ] 支持 OBS 的 Spout/Syphon 视频流输出


