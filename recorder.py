

from mozprofile import create_profile
import os
import sys
import argparse
from recorder.mitmproxy import Mitmproxy
from recorder.MobileApp import MobileApp

from mozlog import commandline, get_default_logger, set_default_logger


class Recorder(object):

    def __init__(self, recording):

        self.config = {}
        self.config['host'] ='127.0.0.1'
        self.config['profile'] = create_profile('firefox')
        self.config['binary'] = "org.mozilla.geckoview_example"
        self.config['app'] = "geckoview"

        self.config['local_profile_dir'] = self.config['profile'].profile

        self.config['recording'] = os.path.join(os.getcwd(), recording)

        self.log = get_default_logger(component='recorder-main - ')

        self.proxy_process = None
        self.device = None

    def start_recoding(self):
        self.log.info("test")
        self.mobile_app = MobileApp(self.config)

        self.mobile_app.setup_app()
        self.proxy_process = Mitmproxy(self.config)

        self.mobile_app.start_app()

        raw_input("Press Enter to continue...")

        self.proxy_process.stop_mitmproxy_playback()

def recorder():


    parser = argparse.ArgumentParser(description='Start and record a mitmProxy recording')
    parser.add_argument('--recording', dest='recording', action='store',
                        default="recording.mp", type=str,
                        help='recording name')

    args = parser.parse_args()
    commandline.setup_logging('recorder', args, {'tbpl': sys.stdout})

    recorder = Recorder(recording=args.recording)
    recorder.start_recoding()


if __name__ == "__main__":
    sys.exit(recorder())
