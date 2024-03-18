"""
Copyright (c) 2024 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.

"""

__author__ = "Aron Donaldson, Baothong Le"
__contributors__ = ""
__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"

from argparse import ArgumentParser
from getpass import getpass
import logging
import soap_session

class HelperObject():
    def __init__(self, args):
        self.args = vars(args)
        self.args["cucm_ip_or_hostname"] = self.args["server"]
        if self.args["v"]:
            self.args["verify_ssl_certificate"] = True
        else:
            self.args["verify_ssl_certificate"] = False
        self.args["list_of_perfmon_counters"] = self.args["counters"]
        self.args["cucm_api_account"] = {
            "username": self.args["username"],
            "password": self.args["password"]
        }
        logging.basicConfig(level=logging.DEBUG)
    

    def get_arg(self, argument):
        return self.args[argument]
    

    def log_info(self, message):
        return logging.info(message)
    

    def log_warning(self, message):
        return logging.warning(message)
    

    def log_error(self, message):
        return logging.error(message)
    

    def log_critical(self, message):
        return logging.critical(message)
    

    def log_debug(self, message):
        return logging.debug(message)


if __name__ == "__main__":
    parser = ArgumentParser(description="This script mimics the Splunk 'helper' object, allowing you to run the 'soap_session.py' script outside of Splunk.")
    parser.add_argument("--server", "-s", help="IP Address or Hostname of the Cisco UCM server.", required=True, )
    parser.add_argument("--username", "-u", help="Username of the Cisco UCM API account.", required=True)
    parser.add_argument("--password", "-p", help="Password of the Cisco UCM API account. If password contains special characters, omit this argument - you will be prompted interactively to enter the password.")
    parser.add_argument("-v", help="Verify Cisco UCM server's SSL Certificate?", action="store_true")
    parser.add_argument("--counters", "-c", help="Comma separated list of Perfmon Counters (format must be <object>\<counter>,<object>\<counter>).", default="Memory\% Mem Used,Processor\% CPU Time")

    args = parser.parse_args()
    if not args.password:
        args.password = getpass("Enter the Cisco UCM API account password: ", stream=None)
    helper = HelperObject(args)
    # print(helper.args)
    session = soap_session.PerfmonServiceSession(helper)
    session.add_counters()
    counter_data_result = session.collect_counters()
    session.close_session()
    counter_data = session.parse_xml_to_json(counter_data_result.content)
    #print(counter_data)