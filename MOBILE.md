# 手机 App 说明

当前手机端实现是 `mobile_app.py`，`main.py` 是 Android/Kivy 打包入口。它使用 Kivy 复用现有 Python 计算逻辑。

## 本地预览

```powershell
python -m pip install -r requirements-mobile.txt
python mobile_app.py
```

## Android 打包

Buildozer 官方主要支持 Linux。Windows 上建议使用 WSL2 或 Linux 虚拟机：

```bash
python3 -m pip install --user buildozer
buildozer android debug
```

生成的 APK 通常在 `bin/` 目录。

## GitHub 自动打包

仓库里已经有 `.github/workflows/android-apk.yml`。推送到 GitHub 后，可以在仓库页面：

1. 打开 `Actions`
2. 选择 `Build Android APK`
3. 点 `Run workflow`
4. 等任务完成后，在任务页面的 `Artifacts` 下载 `suanshu-mahjong-debug-apk`

第一次打包会下载 Android SDK/NDK 和编译依赖，可能需要几十分钟。

## iOS

iOS 打包需要 macOS、Xcode 和 Apple Developer 工具链。当前代码层可以复用，但不能直接在 Windows 上生成 iOS App。
