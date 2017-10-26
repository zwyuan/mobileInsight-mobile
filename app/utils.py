"""
main_utils.py

Define utility variables and functions for apps.
"""


'''
module_name, package_name, ClassName, method_name, ExceptionName,
function_name, GLOBAL_CONSTANT_NAME, global_var_name,
instance_var_name, function_parameter_name, local_var_name
'''

# FIXME(likayo): subprocess module in Python 2.7 is not thread-safe.
# Use subprocess32 instead.
import datetime
import functools
import json
import os
import re
import subprocess
import sys
import time
import traceback

from jnius import autoclass, cast
from mobile_insight import Element

ANDROID_SHELL = "/system/bin/sh"

class ChipsetType:
    """
    Define cellular modem type
    """
    QUALCOMM = 0
    MTK      = 1


class MobileInsightUtils(Element):
    """
    MobileInsight Utility functions for main activity and plugins
    """

    def __init__(self):
        self.ctx        = None
        self.Context    = autoclass('android.content.Context')
        self.pyActivity = autoclass('org.kivy.android.PythonActivity').mActivity
        self.pyService  = autoclass('org.kivy.android.PythonService').mService
        self.mi_path    = self.get_mobileinsight_path()

        if self.pyActivity is not None:
            self.ctx    = self.pyActivity
        elif self.pyService is not None:
            self.ctx    = self.pyService
        else:
            self.log_error("Error!")

        self.mWifiManager      = self.ctx.getSystemService(self.Context.WIFI_SERVICE)
        self.mLocationManager  = self.ctx.getSystemService(self.Context.LOCATION_SERVICE)
        self.mTelephonyManager = self.ctx.getSystemService(self.Context.TELEPHONY_SERVICE)


    def is_rooted(self):
        """
        Check if the phone has been rooted
        """
        su_binary_path = [
            "/sbin/",
            "/system/bin/",
            "/system/xbin/",
            "/data/local/xbin/",
            "/su/bin/",
            "/data/local/bin/",
            "/system/sd/xbin/",
            "/system/bin/failsafe/",
            "/data/local/"]

        for path in su_binary_path:
            if os.path.exists(path + "su"):
                return True

        return False

    def run_root_shell_cmd(self, cmd, wait=False):
        p = subprocess.Popen(
            "su",
            executable = ANDROID_SHELL,
            shell      = True,
            stdin      = subprocess.PIPE,
            stdout     = subprocess.PIPE)
        res, err = p.communicate(cmd + '\n')

        if wait:
            p.wait()
            return res
        else:
            return res


    def run_shell_cmd(self, cmd, wait=False):
        p = subprocess.Popen(
            executable = ANDROID_SHELL,
            shell      = True,
            stdin      = subprocess.PIPE,
            stdout     = subprocess.PIPE)
        res, err = p.communicate(cmd + '\n')

        if wait:
            p.wait()
            return res
        else:
            return res


    def detach_thread(self):
        try:
            jnius.detach()
        except BaseException:
            pass


    def get_mi_context():
        return self.ctx


    def get_cur_version(self):
        """
        Get current apk version string
        """
        pkg_name = self.ctx.getPackageName()
        return str(self.ctx.getPackageManager().getPackageInfo(
                pkg_name, 0).versionName)


    def get_chipset_type(self):
        """
        Determine the type of the chipset

        :returns: an enum of ChipsetType
        """

        """
        MediaTek: [ro.board.platform]: [mt6735m]
        Qualcomm: [ro.board.platform]: [msm8084]
        """
        cmd = "getprop ro.board.platform;"
        res = run_shell_cmd(cmd)
        if res.startswith("mt"):
            return ChipsetType.MTK
        elif res.startswith("msm") or res.startswith("mdm"):
            return ChipsetType.QUALCOMM
        else:
            return None


    def get_phone_id():
        cmd = "service call iphonesubinfo 1"
        out = run_shell_cmd(cmd)
        tup = re.findall("\'.+\'", out)
        tupnum = re.findall("\d+", "".join(tup))
        phoneId = "".join(tupnum)
        return phoneId


    def get_phone_manufacturer(self):
        return autoclass('android.os.Build').MANUFACTURER


    def get_phone_model(self):
        return autoclass('android.os.Build').MODEL


    def get_phone_info(self):
        phone_info = get_phone_id() + '-' + get_phone_manufacturer() + '-' + get_phone_model()
        return phone_info


    def get_operator_info():
        # return telephonyManager.getNetworkOperatorName() + "-" + telephonyManager.getNetworkOperator()
        return self.mTelephonyManager.getNetworkOperator()


    def get_last_known_location(self):
        location = self.mLocationManager.getLastKnownLocation(mLocationManager.GPS_PROVIDER)
        if not location:
            location = self.mLocationManager.getLastKnownLocation(mLocationManager.NETWORK_PROVIDER)
        if location:
            return (location.getLatitude(), location.getLongitude())
        else:
            return None


    def get_current_location():
        return get_last_known_location()


    def get_wifi_status():
        return self.mWifiManager.isWifiEnabled()


    def get_cache_dir(self):
        return str(self.ctx.getCacheDir().getAbsolutePath())


    def get_files_dir(self):
        return str(self.ctx.getFilesDir().getAbsolutePath() + '/app')


    def get_sdcard_path(self):
        """
        Return the sdcard path, or None if not accessible
        """
        Environment = autoclass("android.os.Environment")
        state = Environment.getExternalStorageState()
        if not Environment.MEDIA_MOUNTED == state:
            return None

        sdcard_path = Environment.getExternalStorageDirectory().toString()
        return sdcard_path


    def get_legacy_mobileinsight_path(self):
        """
        Return the root path of MobileInsight, or None if not accessible
        """
        sdcard_path = get_sdcard_path()
        if not sdcard_path:
            return None

        legacy_mobileinsight_path = os.path.join(sdcard_path, "mobile_insight")
        return legacy_mobileinsight_path


    def get_mobileinsight_path(self):
        """
        Return the root path of MobileInsight, or None if not accessible
        """
        sdcard_path = get_sdcard_path()
        if not sdcard_path:
            return None

        mobileinsight_path = os.path.join(sdcard_path, "mobileinsight")
        return mobileinsight_path


    def get_mobileinsight_log_path():
        """
        Return the log path of MobileInsight, or None if not accessible
        """
        if self.mi_path is not None:
            return os.path.join(self.mi_path, "log")
        else:
            return None


    def get_mobileinsight_analysis_path():
        """
        Return the analysis result path of MobileInsight, or None if not accessible
        """
        if self.mi_path is not None:
            return os.path.join(self.mi_path, "analysis")
        else:
            return None


    def get_mobileinsight_log_decoded_path():
        """
        Return the decoded log path of MobileInsight, or None if not accessible
        """
        if self.mi_path is not None:
            return os.path.join(self.mi_path, "decoded")
        else:
            return None


    def get_mobileinsight_log_uploaded_path():
        """
        Return the uploaded log path of MobileInsight, or None if not accessible
        """
        if self.mi_path is not None:
            return os.path.join(self.mi_path, "uploaded")
        else:
            return None


    def get_mobileinsight_cfg_path():
        """
        Return the configuration path of MobileInsight, or None if not accessible
        """
        if self.mi_path is not None:
            return os.path.join(self.mi_path, "cfg")
        else:
            return None


    def get_mobileinsight_db_path():
        """
        Return the database path of MobileInsight, or None if not accessible
        """
        if self.mi_path is not None:
            return os.path.join(self.mi_path, "dbs")
        else:
            return None


    def get_mobileinsight_plugin_path():
        """
        Return the plugin path of MobileInsight, or None if not accessible
        """
        if self.mi_path is not None:
            return os.path.join(self.mi_path, "plugins")
        else:
            return None


    def get_mobileinsight_crash_log_path():
        """
        Return the crash log path of MobileInsight, or None if not accessible
        """
        if self.mi_path is not None:
            return os.path.join(self.mi_path, "crash_logs")
        else:
            return None
