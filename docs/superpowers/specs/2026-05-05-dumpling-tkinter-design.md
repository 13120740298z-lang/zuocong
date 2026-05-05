# Dumpling（团子）桌宠（Python/tkinter）设计说明

## 目标

交付一个可在 Windows 上运行的桌面宠物：

- 透明背景、无边框、始终置顶、初始右下角
- 鼠标拖拽移动
- 右键菜单：聊天 / 散步 / 睡觉 / 退出
- Canvas 全手绘角色与动效（无外部图片依赖）
- 可选 AI 聊天（OpenAI 兼容接口），未配置时使用本地拟人化回复
- 交付文件：`团子.py` + `build.bat`（自动生成 `团子.ico` 并用 PyInstaller 打包单文件 `团子.exe`）

## 技术选型

### 方案 A（推荐）：tkinter + Canvas + Windows 透明色键

- GUI：`tkinter`
- 绘制：`tkinter.Canvas`
- 动画：`after(16, ...)` 的定时循环
- 透明：`root.wm_attributes("-transparentcolor", "#ffffff")` + 窗口/画布背景填充纯白
- 置顶：`root.wm_attributes("-topmost", True)`
- 无边框：`root.overrideredirect(True)`
- AI：标准库 `urllib.request` + 后台线程 + 主线程轮询队列更新 UI（避免 UI 卡死）

优点：零三方依赖、脚本可直接跑、打包简单。  
限制：透明主要靠颜色键，无法实现真正 alpha 半透明（“睡觉半透明”用 stipple/颜色近似）。

### 方案 B：PyQt/PySide（不采用）

可做真 alpha/更强渲染，但依赖大、打包体积更高、上手成本更高，不符合“最性价比”。

## 透明策略（已确认）

- 透明色键：纯白 `#ffffff`
- 窗口背景与 Canvas 背景：纯白（会被系统抠透明）
- 团子主体颜色：使用“偏暖白”而非纯白（例如 `#fff7f0`、`#fff3eb` 等），避免被误透明

## 文件交付

### 1) `团子.py`

单文件脚本，职责划分：

- `App`：创建窗口、Canvas、事件绑定、菜单、主循环调度
- `Renderer`：根据当前状态计算参数并在 Canvas 重新绘制（每帧清空并重绘）
- `StateMachine`：管理 `idle/blink/bounce/think/walk/sleep` 状态、状态持续时间、随机触发器
- `ChatClient`：根据 `API_KEY` 是否为空，选择：
  - mock：返回拟人化短句
  - real：调用 OpenAI 兼容 `/chat/completions`，取 `choices[0].message.content`

关键约束：

- 任何网络请求必须在后台线程进行
- UI 只能在主线程更新（通过队列/after 回调）
- 不输出/打印 API_KEY

### 2) `build.bat`

职责：

1. 设置控制台为 UTF-8（避免中文文件名乱码）
2. 如果不存在 `团子.ico`，用 PowerShell + System.Drawing 生成一个简易圆形团子图标，并将 PNG 嵌入 ICO 容器写盘
3. 安装 PyInstaller（若未安装）
4. 执行单文件无控制台打包：

```
pyinstaller --onefile --noconsole --add-data "团子.ico;." --icon=团子.ico 团子.py
```

## 交互设计

### 拖拽移动

- `ButtonPress-1`：记录 `event.x_root/event.y_root` 与当前窗口坐标
- `B1-Motion`：计算差值并更新 `root.geometry(f"+{x}+{y}")`

### 右键菜单

- `Menu(tearoff=False)`
- `Button-3`：`menu.tk_popup(event.x_root, event.y_root)`

菜单行为：

- 聊天：弹出输入框，进入 `think`，显示“团子正在听~”，AI 回复返回后显示气泡 10 秒，然后回到 `idle`
- 散步：进入 `walk`，窗口向右移动 150px，再返回（并伴随身体左右摇晃）
- 睡觉：进入 `sleep` 3 秒（表情 `><` + 颜色/stipple 模拟半透明），然后恢复 `idle`
- 退出：销毁窗口并退出

## 动画与状态机

### 状态列表

- `idle`：3 秒周期正弦上下浮动 + 呆毛轻摆；随机计时触发 `blink/bounce`
- `blink`：4–8 秒随机触发；眼睛变横线，持续 0.2 秒
- `bounce`：20–30 秒随机触发；两段弹跳（用分段 easing 近似重力）
- `think`：聊天期间；头顶“…”气泡，整体倾斜约 5 度
- `walk`：散步；窗口平移 150px 往返；身体左右摇摆
- `sleep`：3 秒；`><` 表情 + 颜色淡化/stipple

### 帧循环

- 目标帧率：60 FPS（`after(16, ...)`）
- 每帧：
  1. 计算 `t`（相对时间）
  2. 根据状态输出绘制参数（yOffset, tilt, blinkFlag, sway, etc.）
  3. `canvas.delete("all")` 重绘

## 绘制规范（Canvas 手绘）

### 团子本体

- 主体：圆（直径 120）用偏暖白填充
- 光晕：多层略大圆（浅色 + stipple）模拟柔光边缘
- 呆毛：`create_line(..., smooth=True, splinesteps=...)` 曲线
- 眼睛：
  - 常态：两个小黑圆点
  - blink：两条短横线
  - sleep：`><`（两条斜线组合）
- 腮红：两侧椭圆，淡粉色

### 气泡

- `create_oval` 或 `create_polygon` 组合做圆角气泡 + 小尾巴
- `create_text` 绘制内容
- 10 秒后自动隐藏

## 可测试性与验收标准

在 Windows 10/11 上：

- 窗口透明、无边框、置顶，背景与 Canvas 区域完全抠透
- 团子主体不被误透明（偏暖白可见）
- 拖拽随鼠标移动，无明显抖动
- 右键菜单可正常弹出并执行各动作
- `blink/bounce` 按设定随机触发
- 聊天：
  - 未配置 `API_KEY`：返回 mock 回复并显示气泡
  - 配置 `API_KEY/API_URL`：可以请求并显示回复，UI 不冻结

