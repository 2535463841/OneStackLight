import time
import threading
import signal
from utils import shell

from common import log

LOG = log.LOG


class ServiceStatusAgent(object):
    SERVICES = ['httpd', 'neutron-server',
                'neutron-dhcp-agent', 'neutron-l3-agent']

    def __init__(self):
        LOG.info('init ServiceStatusAgent ...')
        self.service_status = {}
        self.need_report = []
        self.stop_sync = False
        self.stop_report = False
        self.systemctl = shell.Systemctl()
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def start(self):
        LOG.info('started ServiceStatusAgent ...')
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
            LOG.info('catch signal: %s', signum)
        self.stop_sync = True
        self.stop_report = True

    def report(self):
        while True:
            if self.stop_report:
                break
            self._report_service_status()
            time.sleep(3)

    def _report_service_status(self):
        if not self.need_report:
            return
        report_num = len(self.need_report)
        report_data = {i: self.service_status.get(i) for i in self.need_report}
        LOG.info('report %s service(s): %s', report_num, report_data)
        del self.need_report[:report_num]

    def sync(self):
        while True:
            if self.stop_sync:
                break
            for service in self.SERVICES:
                new_status = self.systemctl.is_active(service)
                service_status = self.service_status.get(service)
                if (not service_status) or \
                   service_status.get('active') is None or \
                   service_status.get('active') != new_status:
                    self.service_status[service] = {
                        'active': self.systemctl.is_active(service)
                    }
                    self.need_report.append(service)
            time.sleep(3)
