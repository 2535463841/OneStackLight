import time
import threading
import signal
from utils import shell


class ServiceAgent(object):
    SERVICES = ['httpd', 'neutron-server', 'dhcp-agent', 'l3-agent']

    def __init__(self):
        self.service_status = {}
        self.stop_sync = False
        self.stop_report = False
        self.systemctl = shell.Systemctl()
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def start(self):
        report_thread = threading.Thread(target=self.report)
        report_thread.setDaemon(True)
        report_thread.start()

        self.sync()
        # sync_thread = threading.Thread(target=self.sync)
        # sync_thread.setDaemon(False)
        # sync_thread.start()

        # report_thread.join()
        # sync_thread.join()

    def stop(self, signum, frame):
        if signum:
            print 'catch signal:', signum
        self.stop_sync = True
        self.stop_report = True

    def report(self):
        while True:
            if self.stop_report:
                break
            print 'service status:', self.service_status
            time.sleep(3)

    def sync(self):
        while True:
            if self.stop_sync:
                break
            for service in self.SERVICES:
                self.service_status[service] = {
                    'active': self.systemctl.is_active(service)
                }
            time.sleep(3)
