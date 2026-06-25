package com.factory.vehicle

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.webkit.JavascriptInterface
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.File
import java.util.concurrent.TimeUnit

/**
 * 注入到 WebView 的 JS bridge 对象
 * H5 页面通过 window.VehicleNative.xxx() 调用
 *
 * 方法：
 *   - capturePhoto(): 拉起原生相机拍照，返回 {success, base64, path}
 *   - uploadPhoto(base64, postId): 把 base64 上传到后端，返回 {url, filename, size}
 *   - login(username, password): 调用后端登录 API，返回 {access_token, user}
 *   - getServerUrl(): 返回当前配置的服务器地址
 *   - openSettings(): 跳到设置页
 */
class WebAppBridge(private val activity: Activity) {

    private val config = ServerConfig(activity)
    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()

    /** 拍照
     *  拍照成功后只告诉 H5 拍照成功，不再传 base64（避免大字符串 JS bridge 问题）
     *  H5 端会再调 uploadPhoto(photoIndex, postId, callbackName) 上传
     */
    @JavascriptInterface
    fun capturePhoto(callbackName: String) {
        (activity as? MainActivity)?.takePhoto { success, filePath ->
            if (success && filePath != null) {
                // 把路径存到 MainActivity，方便 uploadPhoto 取
                (activity as? MainActivity)?.lastPhotoPath = filePath
                callJsCallback(callbackName, """{"success":true,"path":${quote(filePath)}}""")
            } else {
                callJsCallback(callbackName, """{"success":false,"error":"拍照失败或取消"}""")
            }
        }
    }

    /** 上传照片到后端
     *  注意：base64Data 是大字符串，JS bridge 传 string 有限制
     *  实际我们直接在 MainActivity 拍照时把文件路径 + postId 缓存了，
     *  这里只需要传 photoIndex（"front" / "plate"）即可
     *  Android 端直接调后端上传，不经 H5 中转
     */
    @JavascriptInterface
    fun uploadPhoto(photoIndex: String, postId: Int, callbackName: String) {
        Thread {
            try {
                // photoIndex 是 "front" / "plate"；我们从 MainActivity 取最近的照片路径
                val photoPath = (activity as? MainActivity)?.consumeLastPhotoPath()
                if (photoPath == null) {
                    callJsCallback(callbackName, """{"code":400,"message":"没有可用的照片"}""")
                    return@Thread
                }
                val file = File(photoPath)
                if (!file.exists() || file.length() == 0L) {
                    callJsCallback(callbackName, """{"code":400,"message":"照片文件不存在或为空"}""")
                    return@Thread
                }

                val body = MultipartBody.Builder()
                    .setType(MultipartBody.FORM)
                    .addFormDataPart(
                        "file", file.name,
                        file.asRequestBody("image/jpeg".toMediaTypeOrNull())
                    )
                    .apply { if (postId > 0) addFormDataPart("post_id", postId.toString()) }
                    .build()

                val req = Request.Builder()
                    .url("${config.apiPrefix}/files/photo")
                    .post(body)
                    .apply {
                        val token = config.token
                        if (!token.isNullOrEmpty()) {
                            addHeader("Authorization", "Bearer $token")
                        }
                    }
                    .build()

                android.util.Log.d("VehicleApp", "Uploading photo: ${file.absolutePath} (${file.length()} bytes)")
                client.newCall(req).execute().use { resp ->
                    val text = resp.body?.string() ?: "{}"
                    android.util.Log.d("VehicleApp", "Upload response: ${resp.code} $text")
                    callJsCallback(callbackName, text)
                }
            } catch (e: Exception) {
                android.util.Log.e("VehicleApp", "Upload failed", e)
                callJsCallback(callbackName, """{"code":500,"message":"${e.message}"}""")
            }
        }.start()
    }

    /** 登录：返回后端原始 JSON */
    @JavascriptInterface
    fun login(username: String, password: String, callbackName: String) {
        Thread {
            try {
                val json = JSONObject().apply {
                    put("username", username)
                    put("password", password)
                }
                val body = json.toString().toRequestBody("application/json".toMediaTypeOrNull())
                val req = Request.Builder()
                    .url("${config.apiPrefix}/auth/login")
                    .post(body)
                    .build()

                client.newCall(req).execute().use { resp ->
                    val text = resp.body?.string() ?: "{}"
                    // 成功时把 token 存到本地
                    if (resp.isSuccessful) {
                        runCatching {
                            val data = JSONObject(text).optJSONObject("data")
                            val token = data?.optString("access_token")
                            val user = data?.optJSONObject("user")
                            if (token != null) config.token = token
                            if (username.isNotEmpty()) config.username = username
                            if (user != null) {
                                config.postId = user.optInt("post_id", 0)
                            }
                        }
                    }
                    callJsCallback(callbackName, text)
                }
            } catch (e: Exception) {
                callJsCallback(callbackName, """{"code":500,"message":"${e.message}"}""")
            }
        }.start()
    }

    /** 登出 */
    @JavascriptInterface
    fun logout() {
        config.logout()
    }

    /** 取当前服务器地址（用于 H5 显示） */
    @JavascriptInterface
    fun getServerUrl(): String = config.baseUrl

    /** 跳转设置页 */
    @JavascriptInterface
    fun openSettings() {
        val intent = Intent(activity, SettingsActivity::class.java)
        activity.startActivity(intent)
    }

    /** 拉起拨号（万一需要拨打调度电话） */
    @JavascriptInterface
    fun callPhone(phoneNumber: String) {
        val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:$phoneNumber"))
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        activity.startActivity(intent)
    }

    /** 取 App 信息 */
    @JavascriptInterface
    fun getAppInfo(): String {
        return JSONObject().apply {
            put("platform", "android")
            put("appVersion", "1.0.0")
            put("serverUrl", config.baseUrl)
            put("loggedIn", config.isLoggedIn())
            put("username", config.username ?: "")
        }.toString()
    }

    // ============ helpers ============

    private fun callJsCallback(callbackName: String, data: String) {
        // 全局函数，H5 端必须定义 window[callbackName]
        val js = "if (typeof $callbackName === 'function') { $callbackName($data); } else { console.log('VehicleNative: callback $callbackName not found'); }"
        (activity as? MainActivity)?.let { act ->
            act.runOnUiThread {
                act.findViewById<android.webkit.WebView>(R.id.webView)?.evaluateJavascript(js, null)
            }
        }
    }

    private fun quote(s: String): String = "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"") + "\""
}
