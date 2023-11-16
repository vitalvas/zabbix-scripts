#!/opt/python/zabbix/bin/python

import re
from pyzabbix import ZabbixAPI
from libexec.config import Config
from libexec.telegram import Telegram


class ZabbixAlerts:
    def __init__(self):
        self.config = Config()

        zabbix_conf = self.config.get('zabbix')

        self.zapi = ZabbixAPI(zabbix_conf.get('url'))
        self.zapi.login(zabbix_conf.get('user'), zabbix_conf.get('password'))

        
        self.telegram = None
        telegram_conf = self.config.get('telegram')
        if telegram_conf:
            bot_name = zabbix_conf.get('user')
            self.telegram = Telegram(telegram_conf, prefix=f'[{bot_name}]:')


        self._template_name = [
            'BDCOM xPON Switch SNMP',
            'D-Link DES_DGS Switch SNMP'
        ]
        
        self.patterns = [
            re.compile(r'Interface ([0-9]+)/([0-9]+)\(\):'), # dlink
            re.compile(r'Slot([0-9]+)/([0-9]+)\(Slot([0-9]+)/([0-9]+)\):'), # dlink
            re.compile(r'EPON([0-9]+)/([0-9]+):([0-9]+)\(\):'), # bdcom
            re.compile(r'GigaEthernet([0-9]+)/([0-9]+)\(\):'), # bdcom
        ]

        self.updated = []

    def get_hosts(self):
        host_list = {}
        hosts = self.zapi.host.get(
            output=['hostid', 'host'],
            selectParentTemplates=['templateid', 'name'],
            filter={'status': 0},
            sortfield=['host'],
            sortorder='ASC'
        )
        for host in hosts:
            for tmpl in host.get('parentTemplates', []):
                if tmpl.get('name') in self._template_name:
                    host_list[host.get('hostid')] = host.get('host') 
                break

        return host_list

    def _match_name(self, row):
        for line in self.patterns:
            if line.search(row):
                return True

        return False

    def update_triggers(self, hostid, host):
        ids = {}
        lists = self.zapi.trigger.get(
            hostids=hostid,
            output=['triggerid', 'description', 'status'],
            skipDependent=0
        )
        for row in lists:
            if not row.get('description').lower().startswith('interface'):
                continue

            # disable alerts on interface
            if self._match_name(row.get('description')) and row.get('status') == '0':
                ids[row.get('triggerid')] = '1'

            # enable alerts on interface
            if not self._match_name(row.get('description')) and row.get('status') == '1':
                ids[row.get('triggerid')] = '0'

        if ids:
            print(f'Updating triggers for: {host}')

            self.updated.append(host)

            for triggerid, state in ids.items():
                self.zapi.trigger.update(triggerid=triggerid, status=state)

    def run(self):
        hosts = self.get_hosts()
        for hostid, host in hosts.items():
            self.update_triggers(hostid, host)

        if self.updated and self.telegram:
            self.telegram.send_message(
                "Updated alerts for: " + ', '.join(self.updated)
            )


if __name__ == '__main__':
    ZabbixAlerts().run()

