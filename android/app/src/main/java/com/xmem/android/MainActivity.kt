package com.xmem.android

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private lateinit var baseUrlInput: EditText
    private lateinit var tokenInput: EditText
    private lateinit var statusText: TextView

    /**
     * 初始化主页并绑定按钮行为。
     */
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        bindViews()
        bindActions()
        loadSettings()
        updateStatus(getString(R.string.status_idle))
    }

    /**
     * 绑定页面控件引用。
     */
    private fun bindViews() {
        baseUrlInput = findViewById(R.id.input_base_url)
        tokenInput = findViewById(R.id.input_token)
        statusText = findViewById(R.id.text_status)
    }

    /**
     * 注册按钮点击事件。
     */
    private fun bindActions() {
        val saveButton = findViewById<Button>(R.id.btn_save)
        val captureButton = findViewById<Button>(R.id.btn_capture)

        saveButton.setOnClickListener {
            saveSettings()
            updateStatus(getString(R.string.status_idle))
        }

        captureButton.setOnClickListener {
            startCaptureFlow()
        }
    }

    /**
     * 读取并填充已保存的连接配置。
     */
    private fun loadSettings() {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        baseUrlInput.setText(prefs.getString(KEY_BASE_URL, DEFAULT_BASE_URL))
        tokenInput.setText(prefs.getString(KEY_TOKEN, ""))
    }

    /**
     * 保存当前连接配置到本地。
     */
    private fun saveSettings() {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit()
            .putString(KEY_BASE_URL, baseUrlInput.text.toString().trim())
            .putString(KEY_TOKEN, tokenInput.text.toString().trim())
            .apply()
    }

    /**
     * 启动截图授权流程页面。
     */
    private fun startCaptureFlow() {
        updateStatus(getString(R.string.status_capture))
        val intent = Intent(this, CaptureActivity::class.java)
        startActivity(intent)
    }

    /**
     * 更新页面状态提示文本。
     */
    private fun updateStatus(message: String) {
        statusText.text = message
    }

    companion object {
        private const val PREFS_NAME = "xmem_capture_prefs"
        private const val KEY_BASE_URL = "base_url"
        private const val KEY_TOKEN = "auth_token"
        private const val DEFAULT_BASE_URL = "http://10.0.2.2:8000"
    }
}
