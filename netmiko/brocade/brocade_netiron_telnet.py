"""Brocade Netiron Telnet Driver."""
from __future__ import unicode_literals

import time
from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko import log

from netmiko.netmiko_globals import MAX_BUFFER, BACKSPACE_CHAR
import logging
import re

class BrocadeNetironTelnet(CiscoBaseConnection):

    def session_preparation(self):
        """
        Prepare the session after the connection has been established

        This method handles some differences that occur between various devices
        early on in the session.

        In general, it should include:
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width()
        """
        
        # ckishimo do not test channel - infinte loop reading data
        #self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width()

    def find_prompt(self, delay_factor=1):
        """Finds the current network device prompt, last line only."""
        delay_factor = self.select_delay_factor(delay_factor)
        self.clear_buffer()
        log.debug("ckishimo just changed \n with \r")
        self.write_channel("\r")
        #self.write_channel("\n")
        time.sleep(delay_factor * .1)

        # Initial attempt to get prompt
        prompt = self.read_channel()
        if self.ansi_escape_codes:
            prompt = self.strip_ansi_escape_codes(prompt)

        log.debug("prompt1: {0}".format(prompt))

        # Check if the only thing you received was a newline
        count = 0
        prompt = prompt.strip()
        while count <= 10 and not prompt:
            prompt = self.read_channel().strip()
            if prompt:
                log.debug("prompt2a repr: {0}".format(repr(prompt)))
                log.debug("prompt2b: {0}".format(prompt))
                if self.ansi_escape_codes:
                    prompt = self.strip_ansi_escape_codes(prompt).strip()
            else:
                self.write_channel("\n")
                time.sleep(delay_factor * .1)
            count += 1

        log.debug("prompt3: {0}".format(prompt))
        # If multiple lines in the output take the last line
        prompt = self.normalize_linefeeds(prompt)
        prompt = prompt.split('\n')[-1]
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("Unable to find prompt: {}".format(prompt))
        time.sleep(delay_factor * .1)
        self.clear_buffer()
        return prompt

    def check_enable_mode(self, check_string=''):
        """Check if in enable mode. Return boolean."""
        log.debug("ckishimo replace \n with \r in brocade_netiron_telnet.py")
        self.write_channel('\r')
        #self.write_channel('\n')
        output = self.read_until_prompt()
        log.debug("{0}".format(output))
        return check_string in output

    def disable_paging(self, command="skip-page-display\r", delay_factor=1):
        log.debug("ckishimo in disable_paging in brocade_netiron_telnet.py")
        self.enable()
        log.debug("ckishimo out of enable in disable_paging in brocade_netiron_telnet.py")
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(delay_factor * .1)
        self.clear_buffer()
        command = self.normalize_cmd(command)
        self.write_channel(command)
        output = self.read_until_prompt()
        log.debug("{0}".format(output))
        return output

    def send_command(self, command_string, expect_string=None,
                     delay_factor=1, max_loops=500, auto_find_prompt=True,
                     strip_prompt=True, strip_command=True, normalize=True):
        """Execute command_string on the SSH channel using a pattern-based mechanism. Generally
        used for show commands. By default this method will keep waiting to receive data until the
        network device prompt is detected. The current network device prompt will be determined
        automatically.

        :param command_string: The command to be executed on the remote device.
        :type command_string: str
        :param expect_string: Regular expression pattern to use for determining end of output.
            If left blank will default to being based on router prompt.
        :type expect_str: str
        :param delay_factor: Multiplying factor used to adjust delays (default: 1).
        :type delay_factor: int
        :param max_loops: Controls wait time in conjunction with delay_factor (default: 150).
        :type max_loops: int
        :param strip_prompt: Remove the trailing router prompt from the output (default: True).
        :type strip_prompt: bool
        :param strip_command: Remove the echo of the command from the output (default: True).
        :type strip_command: bool
        :param normalize: Ensure the proper enter is sent at end of command (default: True).
        :type normalize: bool
        """
        delay_factor = self.select_delay_factor(delay_factor)

        log.debug("ckishimo send_command in base_connection")
        # Find the current router prompt
        if expect_string is None:
            if auto_find_prompt:
                try:
                    prompt = self.find_prompt(delay_factor=delay_factor)
                except ValueError:
                    prompt = self.base_prompt
            else:
                prompt = self.base_prompt
            search_pattern = re.escape(prompt.strip())
        else:
            search_pattern = expect_string

        if normalize:
            command_string = self.normalize_cmd(command_string)

        time.sleep(delay_factor * .2)
        self.clear_buffer()
        log.debug("ckishimo add \r in brocade_netiron_telnet.py search pattern %s" % search_pattern)
        self.write_channel(command_string + '\r')

        # Keep reading data until search_pattern is found (or max_loops)
        i = 1
        output = ''
        while i <= max_loops:
            new_data = self.read_channel()
            if new_data:
                output += new_data
                try:
                    lines = output.split("\n")
                    first_line = lines[0]
                    # First line is the echo line containing the command. In certain situations
                    # it gets repainted and needs filtered
                    if BACKSPACE_CHAR in first_line:
                        pattern = search_pattern + r'.*$'
                        first_line = re.sub(pattern, repl='', string=first_line)
                        lines[0] = first_line
                        output = "\n".join(lines)
                except IndexError:
                    pass
                if re.search(search_pattern, output):
                    log.debug("found search_pattern %s in output" % search_pattern)
                    break
            else:
                time.sleep(delay_factor * .2)
            i += 1
        else:   # nobreak
            raise IOError("Search pattern never detected in send_command_expect: {0}".format(
                search_pattern))

        log.debug("out of the loop")
        output = self._sanitize_output(output, strip_command=strip_command,
                                       command_string=command_string, strip_prompt=strip_prompt)
        return output

    def telnet_login(self, pri_prompt_terminator='#', alt_prompt_terminator='>',
                     username_pattern=r"Name: ", pwd_pattern=r"assword: ",
                     delay_factor=1, max_loops=60):
        """Telnet login. Can be username/password or just password."""

        # Add import logging and log everything!
        logging.basicConfig(filename='test.log', level=logging.DEBUG)
        logger = logging.getLogger("netmiko")

        super(BrocadeNetironTelnet, self).telnet_login(
                pri_prompt_terminator=pri_prompt_terminator,
                alt_prompt_terminator=alt_prompt_terminator,
                username_pattern=username_pattern,
                pwd_pattern=pwd_pattern,
                delay_factor=delay_factor,
                max_loops=max_loops)
