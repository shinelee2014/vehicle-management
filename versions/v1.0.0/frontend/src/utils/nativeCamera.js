/**
 * 检测是否在 Android WebView 内运行，并提供原生相机调用
 *
 * 用法：
 *   const photo = await nativeCamera.takePhoto()
 *   if (photo.success) { ... photo.base64 }
 */
export const isAndroidApp = () => {
  return typeof window !== 'undefined' && !!window.VehicleNative
}

/** 通过 Android 原生相机拍照，返回 Promise<{success, base64, path}> */
export const takePhotoNative = () => {
  return new Promise((resolve) => {
    if (!isAndroidApp()) {
      resolve({ success: false, error: 'Not in Android app' })
      return
    }
    // 临时全局函数，Android 拍照完成后调用
    const callbackName = `__photoCallback_${Date.now()}_${Math.random().toString(36).slice(2)}`
    window[callbackName] = (data) => {
      try {
        delete window[callbackName]
      } catch (e) { /* ignore */ }
      resolve(data)
    }
    // 超时保护
    setTimeout(() => {
      if (window[callbackName]) {
        try { delete window[callbackName] } catch (e) { /* ignore */ }
        resolve({ success: false, error: '拍照超时' })
      }
    }, 60_000)
    window.VehicleNative.capturePhoto(callbackName)
  })
}

/** 通过 Android 原生 API 上传照片
 *  Android 端会直接调后端 /files/photo，不再走 base64
 */
export const uploadPhotoNative = (photoIndex, postId) => {
  return new Promise((resolve, reject) => {
    if (!isAndroidApp()) {
      reject(new Error('Not in Android app'))
      return
    }
    const callbackName = `__uploadCallback_${Date.now()}_${Math.random().toString(36).slice(2)}`
    window[callbackName] = (data) => {
      try { delete window[callbackName] } catch (e) { /* ignore */ }
      try {
        const parsed = typeof data === 'string' ? JSON.parse(data) : data
        resolve(parsed)
      } catch (e) {
        resolve(data)
      }
    }
    setTimeout(() => {
      if (window[callbackName]) {
        try { delete window[callbackName] } catch (e) { /* ignore */ }
        reject(new Error('上传超时'))
      }
    }, 60_000)
    // photoIndex 是 "front" / "plate" 标识（用于日志）
    window.VehicleNative.uploadPhoto(photoIndex, postId || 0, callbackName)
  })
}

/** 获取 App 信息（用于调试） */
export const getAppInfo = () => {
  if (!isAndroidApp()) return null
  try {
    return JSON.parse(window.VehicleNative.getAppInfo())
  } catch (e) {
    return null
  }
}

/** 跳转 Android 设置页 */
export const openSettings = () => {
  if (isAndroidApp()) window.VehicleNative.openSettings()
}
