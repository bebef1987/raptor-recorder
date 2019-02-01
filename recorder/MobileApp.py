from mozdevice import ADBAndroid
from mozlog import get_default_logger

import os

class MobileApp():

    def __init__(self, config):
        self.config = config

        self.log = get_default_logger(component='recorder-mobile-app - ')
        self.profile = self.config['profile']

    def setup_app(self):
        # create the android device handler; it gets initiated and sets up adb etc
        self.log.info("creating android device handler using mozdevice")
        self.device = ADBAndroid(verbose=True, logger_name="recorder-adb - ")

        self.device_raptor_dir = "/sdcard/raptor"
        self.config['device_raptor_dir'] = self.device_raptor_dir
        if self.device.is_dir(self.device_raptor_dir):
            self.log.info("deleting existing device raptor dir: %s" % self.device_raptor_dir)
            self.device.rm(self.device_raptor_dir, recursive=True)
            self.log.info("creating raptor folder on sdcard: %s" % self.device_raptor_dir)
        self.device.mkdir(self.device_raptor_dir)
        self.device.chmod(self.device_raptor_dir, recursive=True)

    def start_app(self):
        self.log.info("Adb Port redirect:")
        _tcp_port = "tcp:8080"
        self.device.create_socket_connection('reverse', _tcp_port, _tcp_port)

        userjspath = os.path.join(self.profile.profile, 'user.js')
        with open(userjspath) as userjsfile:
            prefs = userjsfile.readlines()

        prefs = [pref for pref in prefs if 'network.proxy' not in pref]

        with open(userjspath, 'w') as userjsfile:
            userjsfile.writelines(prefs)

        no_proxies_on = "localhost, 127.0.0.1, %s" % self.config['host']
        proxy_prefs = {}
        proxy_prefs["network.proxy.type"] = 1
        proxy_prefs["network.proxy.http"] = self.config['host']
        proxy_prefs["network.proxy.http_port"] = 8080
        proxy_prefs["network.proxy.ssl"] = self.config['host']
        proxy_prefs["network.proxy.ssl_port"] = 8080
        proxy_prefs["network.proxy.no_proxies_on"] = no_proxies_on
        self.profile.set_preferences(proxy_prefs)


        self.device_profile = os.path.join(self.device_raptor_dir, "profile")

        if self.device.is_dir(self.device_profile):
            self.log.info("deleting existing device profile folder: %s" % self.device_profile)
            self.device.rm(self.device_profile, recursive=True)

        self.log.info("creating profile folder on device: %s" % self.device_profile)
        self.device.mkdir(self.device_profile)

        self.log.info("copying firefox profile onto the device")
        self.log.info("note: the profile folder being copied is: %s" % self.profile.profile)
        self.log.info('the adb push cmd copies that profile dir to a new temp dir before copy')
        self.device.push(self.profile.profile, self.device_profile)
        self.device.chmod(self.device_profile, recursive=True)

        # now start the geckoview/fennec app
        self.log.info("starting %s" % self.config['app'])

        extra_args = ["-profile", self.device_profile,
                      "--marionette",
                      "--es", "env0", "LOG_VERBOSE=1",
                      "--es", "env1", "R_LOG_LEVEL=6",
                      ]

        # launch geckoview example app
        try:
            # make sure the geckoview app is not running before
            # attempting to start.
            self.device.stop_application(self.config['binary'])
            self.device.launch_activity(self.config['binary'],
                                        "GeckoViewActivity",
                                        extra_args=extra_args,
                                        url='about:blank',
                                        e10s=True,
                                        fail_if_running=False)
        except Exception:
            self.log.error("Exception launching %s" % self.config['binary'])
            raise