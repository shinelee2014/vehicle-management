# 厂区车辆登记 Android App

基于 WebView 套壳的 Android 应用，把 H5 前端打包成 APK 安装到平板上，保安拿起平板就能直接拍照登记。

## 功能

- **原生相机拍照** — 调用系统相机，比 Web `<input type="file" capture>` 更可靠，支持扫码/对焦
- **可配置服务器地址** — 设置页里改 IP，不用重新打包
- **账号密码登录** — 每个保安用自己的账号，追溯操作人
- **完全离线可用** — 网络断开时 H5 仍能浏览已加载页面

## 项目结构

```
android-app/
├── app/
│   ├── src/main/
│   │   ├── AndroidManifest.xml        # 权限 + Activity 注册
│   │   ├── java/com/factory/vehicle/
│   │   │   ├── VehicleApp.kt          # Application
│   │   │   ├── MainActivity.kt        # WebView 主界面
│   │   │   ├── SettingsActivity.kt    # 设置页（改服务器地址）
│   │   │   ├── ServerConfig.kt        # SharedPreferences 包装
│   │   │   └── WebAppBridge.kt        # JS bridge（拍照/上传/登录）
│   │   └── res/
│   │       ├── layout/                # 布局
│   │       ├── values/                # 字符串/颜色/主题
│   │       ├── drawable/              # 图标
│   │       └── xml/file_paths.xml     # FileProvider 配置
│   ├── build.gradle
│   └── proguard-rules.pro
├── build.gradle
├── settings.gradle
├── gradle.properties
├── gradle/wrapper/gradle-wrapper.properties
└── README.md
```

## 打包步骤

### 1. 安装 Android Studio

下载：https://developer.android.com/studio

### 2. 打开项目

```
Android Studio → Open → 选择 android-app 目录
```

> **首次打开 Android Studio 会自动生成 `gradlew`、`gradlew.bat` 和 `gradle-wrapper.jar`，无需手动创建。**

### 3. 同步 Gradle

第一次打开会自动下载 Gradle Wrapper 和依赖。也可以手动：

```bash
cd android-app
./gradlew assembleRelease    # 生成 release APK
# 或
./gradlew assembleDebug      # 生成 debug APK（更易调试）
```

### 4. 找 APK

- Debug: `android-app/app/build/outputs/apk/debug/app-debug.apk`
- Release: `android-app/app/build/outputs/apk/release/app-release-unsigned.apk`

### 5. 签名（发布版本必须）

```bash
# 生成 keystore
keytool -genkey -v -keystore release.keystore -alias vehicle -keyalg RSA -keysize 2048 -validity 10000

# 签名
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 -keystore release.keystore app-release-unsigned.apk vehicle

# 对齐（用 Android SDK 自带的 zipalign）
zipalign -v 4 app-release-unsigned.apk app-release.apk
```

## 安装到平板

```bash
adb install app-release.apk
# 或覆盖安装
adb install -r app-release.apk
```

## 第一次使用

1. 打开"厂区车辆登记" App
2. 长按顶部导航栏或点击"⚙"按钮 → 设置
3. 修改"后端服务器地址"为 NAS IP，例如 `http://192.168.6.12:8080`
4. 点击"保存并测试连接" — 确认返回 200
5. 回到主界面 → 登录（用 `security1` / `123456` 等）
6. 拍照登记

## 调试技巧

### 看 H5 端的 console.log

在 WebView 里远程调试：连接平板到电脑，Chrome 地址栏输入 `chrome://inspect` → 找到 WebView → 点 inspect。

### 看 App 日志

```bash
adb logcat -s "VehicleApp:*" "WebView:*" "chromium:*"
```

### 修改默认服务器地址

编辑 `ServerConfig.kt` 的 `DEFAULT_BASE_URL` 常量，然后重新打包。

## 注意事项

1. **首次启动会请求相机权限** — 需要允许
2. **HTTP 协议需在 manifest 加 `usesCleartextTraffic="true"`** — 已加好
3. **平板要连厂内 WiFi** — 默认服务器地址只服务内网
4. **如果换 NAS** — 在 App 设置页改 IP 即可，不用重打包

## 后续优化

- [ ] 离线缓存（OkHttp + Room）
- [ ] 二维码扫描（zxing）
- [ ] 推送通知（个推/极光）
- [ ] 自动登录（token 持久化已实现）
- [ ] 平板锁屏后保持登录
