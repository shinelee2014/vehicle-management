package com.factory.vehicle

import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.view.KeyEvent
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import com.factory.vehicle.databinding.ActivityMainBinding
import java.io.File

/**
 * 主界面：用 WebView 加载部署好的前端 H5 页面
 * - 通过 JS bridge 调用原生相机拍照
 * - 通过 ServerConfig 写入 token、用户信息
 */
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var config: ServerConfig

    /** 拍照完成回调 */
    private var pendingPhotoCallback: ((success: Boolean, filePath: String?) -> Unit)? = null
    private var currentPhotoPath: String? = null

    /** 最近拍的照片路径（给 uploadPhoto 用） */
    var lastPhotoPath: String? = null
        @Synchronized get
        @Synchronized set

    /** 取出最近的照片路径（单次取用） */
    fun consumeLastPhotoPath(): String? {
        val p = lastPhotoPath
        // 不清空，允许同一次拍照多次上传（前端/后端调用）
        return p
    }

    private val REQUEST_TAKE_PHOTO = 2001
    private val REQUEST_CAMERA_PERMISSION = 2002
    private val REQUEST_FILE_CHOOSER = 2003

    /** 文件选择器（WebView <input type="file">） */
    private var filePathCallback: ValueCallback<Array<Uri>>? = null

    private fun logToJs(msg: String) {
        // 写日志到 logcat，同时打到 H5 console（如果 WebView 在）
        android.util.Log.d("VehicleApp", msg)
        // 弹 Toast 方便现场看（不用连接调试工具）
        try {
            android.widget.Toast.makeText(this, msg, android.widget.Toast.LENGTH_SHORT).show()
        } catch (_: Exception) {}
        try {
            val safe = msg.replace("\\", "\\\\").replace("'", "\\'")
            binding.webView.evaluateJavascript("console.log('[Android] $safe')", null)
        } catch (e: Exception) { /* ignore */ }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        config = ServerConfig(this)

        // 开启 WebView 远程调试（chrome://inspect 需要）
        WebView.setWebContentsDebuggingEnabled(true)

        setupWebView()
        loadAppUrl()
    }

    private fun setupWebView() {
        binding.webView.apply {
            settings.apply {
                javaScriptEnabled = true
                domStorageEnabled = true
                databaseEnabled = true
                cacheMode = WebSettings.LOAD_DEFAULT
                useWideViewPort = true
                loadWithOverviewMode = true
                setSupportZoom(true)
                builtInZoomControls = true
                displayZoomControls = false
                allowFileAccess = true
                allowContentAccess = true
                mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            }

            webViewClient = WebViewClient()
            webChromeClient = object : WebChromeClient() {
                override fun onShowFileChooser(
                    webView: WebView?,
                    filePathCallback: ValueCallback<Array<Uri>>?,
                    fileChooserParams: FileChooserParams?
                ): Boolean {
                    this@MainActivity.filePathCallback = filePathCallback
                    try {
                        val intent = Intent(Intent.ACTION_GET_CONTENT).apply {
                            type = "image/*"
                            addCategory(Intent.CATEGORY_OPENABLE)
                            putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true)
                        }
                        startActivityForResult(
                            Intent.createChooser(intent, "选择照片"),
                            REQUEST_FILE_CHOOSER
                        )
                    } catch (e: Exception) {
                        logToJs("file chooser error: ${e.message}")
                        filePathCallback?.onReceiveValue(null)
                        this@MainActivity.filePathCallback = null
                    }
                    return true
                }
            }

            // 注入 JS bridge
            addJavascriptInterface(WebAppBridge(this@MainActivity), "VehicleNative")
        }
    }

    private fun loadAppUrl() {
        val url = config.baseUrl
        binding.webView.loadUrl(url)
    }

    /**
     * 启动原生相机拍照（公开给 WebAppBridge）
     * 用经典 startActivityForResult 而非 ActivityResultContracts，
     * 兼容性更好，更容易排查问题
     */
    fun takePhoto(callback: (success: Boolean, filePath: String?) -> Unit) {
        logToJs("takePhoto() called")

        // 1. 先检查权限
        if (checkSelfPermission(android.Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            logToJs("CAMERA not granted, requesting...")
            pendingPhotoCallback = callback
            requestPermissions(
                arrayOf(android.Manifest.permission.CAMERA),
                REQUEST_CAMERA_PERMISSION
            )
            return
        }
        logToJs("CAMERA granted, launching camera intent...")

        // 2. 创建输出文件
        val photoFile = try {
            File.createTempFile(
                "vehicle_${System.currentTimeMillis()}",
                ".jpg",
                externalCacheDir ?: cacheDir
            )
        } catch (e: Exception) {
            logToJs("createTempFile failed: ${e.message}")
            callback(false, null)
            return
        }

        currentPhotoPath = photoFile.absolutePath
        pendingPhotoCallback = callback

        val photoUri = try {
            FileProvider.getUriForFile(
                this,
                "${packageName}.fileprovider",
                photoFile
            )
        } catch (e: Exception) {
            logToJs("FileProvider failed: ${e.message}")
            callback(false, null)
            pendingPhotoCallback = null
            currentPhotoPath = null
            return
        }
        logToJs("photoUri=$photoUri, file=${photoFile.absolutePath}")

        // 3. 启动相机 Intent
        try {
            val intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE).apply {
                putExtra(MediaStore.EXTRA_OUTPUT, photoUri)
                addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            // 授予所有相机应用写权限
            val resInfoList = packageManager.queryIntentActivities(intent, PackageManager.MATCH_DEFAULT_ONLY)
            for (info in resInfoList) {
                grantUriPermission(
                    info.activityInfo.packageName,
                    photoUri,
                    Intent.FLAG_GRANT_WRITE_URI_PERMISSION or Intent.FLAG_GRANT_READ_URI_PERMISSION
                )
            }
            startActivityForResult(intent, REQUEST_TAKE_PHOTO)
            logToJs("startActivityForResult sent, waiting for camera...")
        } catch (e: Exception) {
            logToJs("startActivityForResult failed: ${e.javaClass.simpleName}: ${e.message}")
            e.printStackTrace()
            callback(false, null)
            pendingPhotoCallback = null
            currentPhotoPath = null
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_CAMERA_PERMISSION) {
            val cb = pendingPhotoCallback
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                logToJs("CAMERA permission granted after request")
                if (cb != null) {
                    pendingPhotoCallback = null
                    takePhoto(cb)
                }
            } else {
                logToJs("CAMERA permission DENIED by user")
                pendingPhotoCallback = null
                cb?.invoke(false, null)
            }
        }
    }

    @Deprecated("经典 API 兼容性更好，保留以支持 FileProvider + 系统相机")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        logToJs("onActivityResult: code=$requestCode, result=$resultCode")
        when (requestCode) {
            REQUEST_TAKE_PHOTO -> {
                val cb = pendingPhotoCallback
                val path = currentPhotoPath
                pendingPhotoCallback = null
                currentPhotoPath = null

                if (resultCode == Activity.RESULT_OK) {
                    // 关键：检查文件实际是否存在 + 大小
                    val file = if (path != null) File(path) else null
                    val exists = file?.exists() ?: false
                    val size = file?.length() ?: 0
                    logToJs("Photo result: exists=$exists size=$size path=$path")

                    if (exists && size > 0) {
                        logToJs("Photo OK: $path ($size bytes)")
                        cb?.invoke(true, path)
                    } else {
                        // 文件没生成 — 很多相机 App 把图存在自己相册里，没写回我们的 URI
                        // 兜底：从相册取最新一张
                        logToJs("File missing! Trying fallback: query MediaStore for latest photo...")
                        val fallbackPath = tryGetLatestPhoto()
                        if (fallbackPath != null) {
                            logToJs("Fallback OK: $fallbackPath")
                            cb?.invoke(true, fallbackPath)
                        } else {
                            logToJs("Fallback also failed")
                            cb?.invoke(false, null)
                        }
                        if (path != null) try { File(path).delete() } catch (_: Exception) {}
                    }
                } else {
                    logToJs("Photo cancelled, resultCode=$resultCode")
                    cb?.invoke(false, null)
                    if (path != null) {
                        try { File(path).delete() } catch (_: Exception) {}
                    }
                }
            }
            REQUEST_FILE_CHOOSER -> {
                val cb = filePathCallback
                filePathCallback = null
                if (cb == null) return
                if (resultCode != Activity.RESULT_OK) {
                    cb.onReceiveValue(null)
                    return
                }
                val uris = mutableListOf<Uri>()
                if (data?.clipData != null) {
                    val clip = data.clipData!!
                    for (i in 0 until clip.itemCount) {
                        uris.add(clip.getItemAt(i).uri)
                    }
                } else if (data?.data != null) {
                    uris.add(data.data!!)
                }
                cb.onReceiveValue(uris.toTypedArray())
            }
        }
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        if (keyCode == KeyEvent.KEYCODE_BACK && binding.webView.canGoBack()) {
            binding.webView.goBack()
            return true
        }
        return super.onKeyDown(keyCode, event)
    }

    override fun onDestroy() {
        binding.webView.destroy()
        super.onDestroy()
    }

    /**
     * 兜底方案：当相机 App 没把图写到我们指定的 FileProvider 路径时，
     * 从 MediaStore 取最新一张照片
     */
    private fun tryGetLatestPhoto(): String? {
        return try {
            val projection = arrayOf(
                android.provider.MediaStore.Images.Media._ID,
                android.provider.MediaStore.Images.Media.DATA,
                android.provider.MediaStore.Images.Media.DATE_ADDED
            )
            val sortOrder = "${android.provider.MediaStore.Images.Media.DATE_ADDED} DESC"
            contentResolver.query(
                android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
                projection, null, null, sortOrder
            )?.use { cursor ->
                if (cursor.moveToFirst()) {
                    val dataCol = cursor.getColumnIndex(android.provider.MediaStore.Images.Media.DATA)
                    val path = cursor.getString(dataCol)
                    if (path != null && File(path).exists()) {
                        // 复制到我们 cache 目录，避免路径问题
                        val target = File(externalCacheDir ?: cacheDir, "fallback_${System.currentTimeMillis()}.jpg")
                        java.io.FileInputStream(path).use { input ->
                            target.outputStream().use { out -> input.copyTo(out) }
                        }
                        target.absolutePath
                    } else null
                } else null
            }
        } catch (e: Exception) {
            logToJs("tryGetLatestPhoto error: ${e.message}")
            null
        }
    }
}
