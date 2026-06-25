package com.factory.vehicle

import android.content.Context
import android.content.SharedPreferences

/**
 * 服务器配置：URL、登录账号、token、岗亭 id
 * 存到 SharedPreferences 里，用户可在设置页修改
 */
class ServerConfig(context: Context) {

    private val prefs: SharedPreferences =
        context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    /** 后端 API 基础地址，例如 http://192.168.6.12:8080 */
    var baseUrl: String
        get() = prefs.getString(KEY_BASE_URL, DEFAULT_BASE_URL) ?: DEFAULT_BASE_URL
        set(value) = prefs.edit().putString(KEY_BASE_URL, value).apply()

    /** API 路径前缀（与后端约定） */
    val apiPrefix: String get() = "$baseUrl/api/v1"

    /** 当前登录的用户名（保安/主管/管理员） */
    var username: String?
        get() = prefs.getString(KEY_USERNAME, null)
        set(value) = prefs.edit().putString(KEY_USERNAME, value).apply()

    /** 后端签发的 JWT */
    var token: String?
        get() = prefs.getString(KEY_TOKEN, null)
        set(value) = prefs.edit().putString(KEY_TOKEN, value).apply()

    /** 当前用户默认岗亭 id（保安专用） */
    var postId: Int
        get() = prefs.getInt(KEY_POST_ID, 0)
        set(value) = prefs.edit().putInt(KEY_POST_ID, value).apply()

    /** 是否已登录（token 非空） */
    fun isLoggedIn(): Boolean = !token.isNullOrEmpty()

    fun logout() {
        prefs.edit()
            .remove(KEY_TOKEN)
            .remove(KEY_USERNAME)
            .remove(KEY_POST_ID)
            .apply()
    }

    companion object {
        private const val PREFS_NAME = "vehicle_server_config"
        private const val KEY_BASE_URL = "base_url"
        private const val KEY_USERNAME = "username"
        private const val KEY_TOKEN = "token"
        private const val KEY_POST_ID = "post_id"

        /** 默认值指向部署好的 NAS，用户首次启动可改 */
        const val DEFAULT_BASE_URL = "http://192.168.6.12:8080"
    }
}
