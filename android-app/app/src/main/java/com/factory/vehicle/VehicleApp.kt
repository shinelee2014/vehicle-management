package com.factory.vehicle

import android.app.Application

/**
 * 应用入口
 */
class VehicleApp : Application() {
    override fun onCreate() {
        super.onCreate()
        instance = this
    }

    companion object {
        lateinit var instance: VehicleApp
            private set
    }
}
