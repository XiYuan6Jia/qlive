# qlive — 弹幕驱动的桌面动画播放器 / 轻量虚拟形象

一个面向直播间互动的桌面动画播放器（或轻量虚拟形象）。它能接收直播弹幕/事件并触发本地动画、声音或动作，用于增强直播互动体验或作为桌面挂件/虚拟形象展示。

核心特点

- 实时接收并解析直播弹幕（示例脚本：`get_danmu.py`）。
- 根据弹幕或本地输入触发动画（支持 GIF/逐帧动画资源目录 `animations/`）。
- 简单的麦克风/音频示例（`mic1.py`, `mic2.py`）用于驱动表情或动作。
- 键盘与热键控制（`keyboarding.py`）便于本地调试与控制。
- 可扩展：你可以将响应逻辑替换为 TTS、OSC、WebSocket 通知或其它自定义动作。

目录概览

- `client.py`：示例客户端/测试脚本。
- `get_danmu.py`：连接直播弹幕源并解析消息。
- `gif_to_frames.py`：把 GIF 拆分为帧供播放器使用。
- `keyboarding.py`：键盘事件与热键处理。
- `mic1.py`, `mic2.py`：麦克风输入演示与不同处理方式。
- `qlive.py`, `qlive2.py`：项目主入口/实验版入口（启动程序）。
- `animations/`：放置动画帧或资源的文件夹。

快速开始（Windows）

建议在虚拟环境中运行：

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

若无 `requirements.txt`，可先安装基础依赖：

```powershell
pip install pygame requests websocket-client
```

运行主程序示例：

```powershell
.\\.venv\\Scripts\\Activate.ps1
python qlive2.py
```

或

```powershell
python qlive.py
```

配置

若需连接第三方弹幕/房间 API，请在仓库根目录创建 `credential.json`（或按脚本内说明编辑）例如：

```json
{
  "provider": "example",
  "room_id": "12345",
  "token": "your_token"
}
```

安全提示：请将包含密钥的文件加入 `.gitignore`，不要将真实凭证推送到公共仓库。

定制与扩展建议

- 将 `get_danmu.py` 中的解析逻辑替换为你的弹幕服务实现（例如斗鱼/哔哩哔哩/自定义 WebSocket）。
- 在 `qlive2.py` 中集成动作映射表：弹幕关键词 -> 动画/音效/动作。
- 增加一个简单的 GUI 设置面板以控制热键、动画映射与日志级别。

贡献与开发者提示

- 若添加新依赖，请在 `requirements.txt` 中列出并提交。
- 提交前确保不含敏感凭证；建议提供最小可复现示例以便审查。

下一步（可选）

- 我可以为你生成 `requirements.txt`（扫描项目导入并推测依赖），或添加运行示例和截图。
- 想要哪些示例：`requirements.txt`、演示动画、还是一个简单的弹幕->动画映射示例？告诉我你的选择。


