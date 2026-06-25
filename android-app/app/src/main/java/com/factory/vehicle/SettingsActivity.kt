package com.factory.vehicle

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.factory.vehicle.databinding.ActivitySettingsBinding

/**
 * 设置页：修改后端服务器地址、查看当前账号
 */
class SettingsActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySettingsBinding
    private lateinit var config: ServerConfig

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySettingsBinding.inflate(layoutInflater)
        setContentView(binding.root)
        config = ServerConfig(this)

        // 显示当前配置
        binding.editServerUrl.setText(config.baseUrl)
        binding.textUsername.text = "当前用户：${config.username ?: "未登录"}"
        binding.textPostId.text = "岗亭 ID：${if (config.postId > 0) config.postId.toString() else "未设置"}"

        binding.btnSave.setOnClickListener {
            val newUrl = binding.editServerUrl.text.toString().trim()
            if (newUrl.isEmpty()) {
                binding.editServerUrl.error = "服务器地址不能为空"
                return@setOnClickListener
            }
            if (!newUrl.startsWith("http://") && !newUrl.startsWith("https://")) {
                binding.editServerUrl.error = "必须以 http:// 或 https:// 开头"
                return@setOnClickListener
            }
            // 去掉末尾的 /
            val cleanUrl = newUrl.trimEnd('/')
            config.baseUrl = cleanUrl
            binding.textStatus.text = "已保存：$cleanUrl\n重启 App 后生效"

            // 测试连接
            testConnection(cleanUrl)
        }

        binding.btnLogout.setOnClickListener {
            config.logout()
            binding.textUsername.text = "当前用户：未登录"
            binding.textStatus.text = "已登出"
        }

        binding.btnBack.setOnClickListener {
            finish()
        }
    }

    private fun testConnection(baseUrl: String) {
        binding.textStatus.text = "正在测试连接..."
        Thread {
            try {
                val client = okhttp3.OkHttpClient.Builder()
                    .connectTimeout(5, java.util.concurrent.TimeUnit.SECONDS)
                    .build()
                val req = okhttp3.Request.Builder()
                    .url("$baseUrl/api/v1/posts/")  // 用一个公开端点测试
                    .get()
                    .build()
                client.newCall(req).execute().use { resp ->
                    val code = resp.code
                    runOnUiThread {
                        binding.textStatus.text = "连接测试：HTTP $code\n${if (code in 200..499) "✓ 服务器可达" else "✗ 服务器异常"}"
                    }
                }
            } catch (e: Exception) {
                runOnUiThread {
                    binding.textStatus.text = "连接失败：${e.message}\n请检查 IP、端口、网络"
                }
            }
        }.start()
    }
}
