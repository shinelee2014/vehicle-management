# ProGuard 规则
-keepattributes *Annotation*
-keepattributes Signature

# OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**

# Android WebView bridge
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
