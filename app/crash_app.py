import kivy
kivy.require('1.0.9')

from kivy.lang import Builder
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.properties import *

import httplib
import urllib
import urllib2
import subprocess
import os
import sys
import re
import datetime
from mi_utils import MobileInsightUtils as miutils

__all__ = ["ConfirmPopup", "CrashApp"]

Builder.load_string('''
<ConfirmPopup>:
    cols:1
    Label:
        text: root.text
    GridLayout:
        cols: 2
        size_hint_y: None
        height: '44sp'
        Button:
            text: 'Yes'
            on_release: root.dispatch('on_answer','yes')
        Button:
            text: 'No'
            on_release: root.dispatch('on_answer', 'no')
''')


class ConfirmPopup(GridLayout):
    text = StringProperty()

    def __init__(self, **kwargs):
        self.register_event_type('on_answer')
        super(ConfirmPopup, self).__init__(**kwargs)

    def on_answer(self, *args):
        pass


class CrashApp(App):
    def build(self):
        content = ConfirmPopup(text='Would you like to report this bug to us?')
        content.bind(on_answer=self._on_answer)
        self.popup = Popup(title="Opps! MobileInsight exits unexpectedly...",
                           content=content,
                           size_hint=(None, None),
                           size=(1200, 600),
                           auto_dismiss=False)
        self.popup.open()

    def __upload_crash_log(self, file_path):

        # http_url = 'http://metro.cs.ucla.edu/mobile_insight/upload_crash_log.php'
        http_url = 'http://mobileinsight.net/upload_crash_log.php'

        # Find log path
        tmp_index = file_path.rfind('/')
        file_name = file_path[tmp_index + 1:]

        # Tokens for http POST
        boundary = "----WebKitFormBoundaryEOdH94ZkJz9PCjBh"
        twoHyphens = "--"
        lineEnd = "\r\n"

        # Read the crash log (as http body)
        data = []

        fr = open(file_path, 'r')
        data.append(twoHyphens + boundary)
        data.append(
            'Content-Disposition: form-data; name="file[]";filename="' +
            file_name +
            '"')
        data.append('Content-Type: application/octet-stream' + lineEnd)
        data.append(fr.read())
        # data.append(lineEnd)
        fr.close()

        data.append(twoHyphens + boundary)
        data.append('Content-Disposition: form-data;name="submit"' + lineEnd)
        data.append('0x11dd')

        data.append(twoHyphens + boundary + twoHyphens + lineEnd)

        http_body = '\r\n'.join(data)

        try:
            # buld http request
            req = urllib2.Request(http_url)
            # header
            req.add_header('Host', 'metro.cs.ucla.edu')
            req.add_header('Cache-Control', 'max-age=0')
            req.add_header(
                'Accept',
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
            req.add_header('Accept-Encoding', 'gzip, deflate')
            req.add_header('Connection', 'keep-alive')
            req.add_header(
                'Content-Type',
                'multipart/form-data; boundary=%s' %
                boundary)
            # req.add_header('file[]',file_name)
            req.add_data(http_body)

            # post data to server
            resp = urllib2.urlopen(req, timeout=5)
            # get response
            if resp:
                qrcont = resp.read()

        except Exception as e:
            "Fail to send bug report!"
            import traceback
            print str(traceback.format_exc())

    def _on_answer(self, instance, answer):
        if answer == "yes":
            phone_info = miutils.get_phone_info()
            log_name = "crash_report_" \
                + phone_info + '_' \
                + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') \
                + '.txt'
            log_name = os.path.join(
                miutils.get_mobileinsight_crash_log_path(), log_name)
            miutils.run_shell_cmd(
                'logcat -d | grep -E "python|diag" >' + log_name, True)
            self.__upload_crash_log(log_name)

        self.popup.dismiss()

        sys.exit(1)
