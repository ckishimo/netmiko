"""Brocade Netiron Telnet Driver."""
from __future__ import unicode_literals

import time
from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko import log

class BrocadeNetironTelnet(CiscoBaseConnection):

    def disable_paging(self, command="skip-page-display", delay_factor=1):
        self.enable()
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(delay_factor * .1)
        self.clear_buffer()
        command = self.normalize_cmd(command)
        self.write_channel(command)
        output = self.read_until_prompt()
        log.debug("{0}".format(output))
        return output

    def telnet_login(self, pri_prompt_terminator='#', alt_prompt_terminator='>',
                     username_pattern=r"Login:", pwd_pattern=r"assword:",
                     delay_factor=1, max_loops=60):
        """Telnet login. Can be username/password or just password."""
        super(BrocadeNetironConnectTelnet, self).telnet_login(
                pri_prompt_terminator=pri_prompt_terminator,
                alt_prompt_terminator=alt_prompt_terminator,
                username_pattern=username_pattern,
                pwd_pattern=pwd_pattern,
                delay_factor=delay_factor,
                max_loops=max_loops)
