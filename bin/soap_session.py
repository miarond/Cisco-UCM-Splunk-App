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

import sys
from datetime import datetime as dt
from datetime import timezone as tz

# External packages
import requests
from lxml import etree
import xml_docs

class PerfmonServiceSession:
    def __init__(self, helper):
        """
        Constructor function to build the PerfmonServiceSession class. 
        This class takes in configuration data from the "helper" function provided by Splunk, parses static XML payloads, and establishes an authenticated session with the target Cisco Call Manager server.

        params: self, helper (Splunk config helper object)
        """
        self.helper = helper
        self.cucm = self.helper.get_arg('cucm_ip_or_hostname')
        self.base_url = f'https://{self.cucm}:8443/perfmonservice2/services/PerfmonService'
        if self.helper.get_arg('verify_ssl_certificate') == True:
            self.ssl_verify = True
        else:
            self.ssl_verify = False
        # Parse CSV string of counters into a List
        self.perfmon_counters = self.__parse_counters()

        # Pre-parse XML Payloads
        self.xml_payload = {
            'perfmonOpenSession': etree.fromstring(xml_docs.perfmonOpenSession),
            'perfmonAddCounter': etree.fromstring(xml_docs.perfmonAddCounter),
            'perfmonCollectCounterData': etree.fromstring(xml_docs.perfmonCollectCounterData),
            'perfmonCollectSessionData': etree.fromstring(xml_docs.perfmonCollectSessionData),
            'perfmonListCounter': etree.fromstring(xml_docs.perfmonListCounter),
            'perfmonCloseSession': etree.fromstring(xml_docs.perfmonCloseSession)
        }
        
        if self.helper.get_arg('cucm_api_account')['username'] == None or self.helper.get_arg('cucm_api_account')['password'] == None:
            self.helper.log_critical('Cisco UCM API Account username or password could not be found. Exiting script...')
            sys.exit(1)

        self.session, self.session_id = self.open_session(self.helper.get_arg('cucm_api_account')['username'], self.helper.get_arg('cucm_api_account')['password'])
    

    def __parse_counters(self):
        """
        Attempt to parse the string of provided Perfmon API counters into a List
        and prepend the CUCM IP or Hostname to each one.
        
        params: self
        returns: perfmon_counters (list)
        """
        counters = self.helper.get_arg('list_of_perfmon_counters')
        if counters == None or len(counters) == 0:
            self.helper.log_critical('Provided list of Cisco UCM Performance Monitoring API counters appears to be empty.')
            sys.exit(1)
        if '\\' not in counters:
            self.helper.log_critical(f'Provided list of Cisco UCM Performance Monitoring API counters may be incorrectly formatted (no backslash characters found):\n{counters}')
            sys.exit(1)
        perfmon_counters = []
        for counter in counters.split(','):
            # Counter string must start with a double backslash, and each backslash must be escaped with another backslash, hence 4 of them.
            counter = f'\\\\{self.cucm}\\{counter}'
            # Ensure that backslashes are properly escaped (arg1 = a single backslash escaped, arg2 = literal double backslash)
            counter.replace('\\', '\\')
            perfmon_counters.append(counter)
        self.helper.log_debug(f'__parse_counters List result:\n{perfmon_counters}')
        return perfmon_counters

    
    def open_session(self, username, password):
        """
        Creates a requests soap_session object and opens a soap_session with PerfMon API.
    
        params: self, username (str), password (str)
        returns: soap_session (requests soap_session object), session_id (str)
        """
        soap_session = requests.Session()
        soap_session.auth = (username, password)

        headers = {
            'Accept': 'text/xml',
            'Content-Type': 'text/xml'
        }
        try:
            result = soap_session.post(self.base_url, data=etree.tostring(self.xml_payload['perfmonOpenSession']).decode('utf-8'), headers=headers, verify=self.ssl_verify)
        except Exception as e:
            self.helper.log_critical(f'Error encountered while establishing session with Cisco UCM Performance Monitoring API:\n{e}')
            sys.exit(1)
        self.helper.log_debug(f'open_session Method Result:\nResponse Status: {result.status_code}\nResponse Headers: {result.headers}\nResponse Body: {result.text}')
        if result.status_code != 200:
            self.helper.log_critical(f'Return code from Cisco UCM Performance Monitoring API was not 200:\nStatus Code: {result.status_code}\nHeaders: {result.headers}\nBody: {result.text}')
            sys.exit(1)
        try:
            parsed = etree.fromstring(result.content)
            result_tree = etree.ElementTree(parsed)
        except Exception as e:
            self.helper.log_critical(f'Error encountered while attempting to parse XML response from Cisco UCM Performance Monitoring API - perfmonOpenSession:\n{e}')
            sys.exit(1)
        
        session_id = result_tree.xpath("//*[local-name()='perfmonOpenSessionReturn']")[0].text
        if session_id == None or len(session_id) == 0:
            self.helper.log_critical(f'Session ID could not be found in XML response from Cisco UCM Performance Monitoring API - perfmonOpenSession:\n{result.text}')
            sys.exit(1)

        return soap_session, session_id
    

    def add_counters(self):
        """
        Builds XML payload and adds Counters via PerfMon API

        params: self
        returns: result (requests Response object)
        """
        # Insert Session ID into XML Payload
        try:
            self.xml_payload['perfmonAddCounter'].xpath("//*[local-name()='SessionHandle']")[0].text = self.session_id
        except Exception as e:
            self.helper.log_critical(f'Error encountered while adding Session ID to perfmonAddCounter XML payload:\n{e}')
            sys.exit(1)
        
        index = 0
        # Obtain the parent tag from the XML payload
        array = self.xml_payload['perfmonAddCounter'].xpath("//*[local-name()='ArrayOfCounter']")[0]
        for counter in self.perfmon_counters:
            # First child tag already exists, so we add first counter to it
            if index == 0:
                array.xpath("//*[local-name()='Name']")[0].text = counter
            # Subsequent child tags must be created and counters added to them
            else:
                new_counter = etree.Element("{http://schemas.cisco.com/ast/soap}Counter")
                subelement = etree.Element("{http://schemas.cisco.com/ast/soap}Name")
                subelement.text = counter
                new_counter.insert(1, subelement)
                array.insert(index, new_counter)
            index += 1
        self.helper.log_debug(f'add_counters Method XML payload:\n{etree.tostring(self.xml_payload["perfmonAddCounter"]).decode("utf-8")}')
        headers = {
            'Accept': 'text/xml',
            'Content-Type': 'text/xml'
        }
        # Send SOAP API call to CUCM, validate response.
        try:
            result = self.session.post(self.base_url, data=etree.tostring(self.xml_payload['perfmonAddCounter']).decode('utf-8'), headers=headers, verify=self.ssl_verify)
        except Exception as e:
            self.helper.log_critical(f'Error encountered while adding counters with Cisco UCM Performance Monitoring API:\n{e}')
            sys.exit(1)
        self.helper.log_debug(f'add_counters Method Result:\nResponse Status: {result.status_code}\nResponse Headers: {result.headers}\nResponse Body: {result.text}')
        if result.status_code != 200:
            self.helper.log_critical(f'Return code from Cisco UCM Performance Monitoring API was not 200:\nStatus Code: {result.status_code}\nHeaders: {result.headers}\nBody: {result.text}')
            sys.exit(1)
        return result


    def collect_counters(self):
        """
        Collects counter values and metadata for the current session.

        params: self
        returns: result (requests Response object)
        """
        # Insert Session ID into XML Payload
        try:
            self.xml_payload['perfmonCollectSessionData'].xpath("//*[local-name()='SessionHandle']")[0].text = self.session_id
        except Exception as e:
            self.helper.log_critical(f'Error encountered while adding Session ID to perfmonCollectSessionData XML payload:\n{e}')
            sys.exit(1)
        self.helper.log_debug(f'collect_counters Method XML payload:\n{etree.tostring(self.xml_payload["perfmonCollectSessionData"]).decode("utf-8")}')
        headers = {
            'Accept': 'text/xml',
            'Content-Type': 'text/xml'
        }
        try:
            result = self.session.post(self.base_url, data=etree.tostring(self.xml_payload['perfmonCollectSessionData']).decode('utf-8'), headers=headers, verify=self.ssl_verify)
        except Exception as e:
            self.helper.log_critical(f'Error encountered while collecting counters from Cisco UCM Performance Monitoring API:\n{e}')
            sys.exit(1)
        self.helper.log_debug(f'collect_counters Method Result:\nResponse Status: {result.status_code}\nResponse Headers: {result.headers}\nResponse Body: {result.text}')
        if result.status_code != 200:
            self.helper.log_critical(f'Return code from Cisco UCM Performance Monitoring API was not 200:\nStatus Code: {result.status_code}\nHeaders: {result.headers}\nBody: {result.text}')
            sys.exit(1)
        return result
    

    def close_session(self):
        """
        Close the SOAP session.

        params: self
        returns: result (requests Response object)
        """
        # Insert Session ID into XML Payload
        try:
            self.xml_payload['perfmonCloseSession'].xpath("//*[local-name()='SessionHandle']")[0].text = self.session_id
        except Exception as e:
            self.helper.log_critical(f'Error encountered while adding Session ID to perfmonCloseSession XML payload:\n{e}')
            sys.exit(1)
        self.helper.log_debug(f'close_session Method XML payload:\n{etree.tostring(self.xml_payload["perfmonCloseSession"]).decode("utf-8")}')
        headers = {
            'Accept': 'text/xml',
            'Content-Type': 'text/xml'
        }
        try:
            result = self.session.post(self.base_url, data=etree.tostring(self.xml_payload['perfmonCloseSession']).decode('utf-8'), headers=headers, verify=self.ssl_verify)
        except Exception as e:
            self.helper.log_critical(f'Error encountered while closing session with Cisco UCM Performance Monitoring API:\n{e}')
            sys.exit(1)
        self.helper.log_debug(f'close_session Method Result:\nResponse Status: {result.status_code}\nResponse Headers: {result.headers}\nResponse Body: {result.text}')
        if result.status_code != 200:
            self.helper.log_critical(f'Return code from Cisco UCM Performance Monitoring API was not 200:\nStatus Code: {result.status_code}\nHeaders: {result.headers}\nBody: {result.text}')
            sys.exit(1)
        return result


    def parse_xml_to_json(self, xml_data):
        """
        Parses the XML counter response data and converts it to JSON format.

        params: self, xml_data (str)
        returns: json_output (list)
        """
        try:
            tree = etree.fromstring(xml_data)
            counters = tree.xpath("//*[local-name()='perfmonCollectSessionDataResponse']")[0]
        except Exception as e:
            self.helper.log_critical(f'Error encountered while parsing counter data from XML payload:\n{e}')
            sys.exit(1)
        
        json_output = []
        for child in counters.iterchildren():
            name_list = child.xpath("./*[local-name()='Name']")[0].text.replace("\\\\", "").split("\\")
            value = child.xpath("./*[local-name()='Value']")[0].text
            cstatus = child.xpath("./*[local-name()='CStatus']")[0].text
            counter_dict = {
                'timestamp': dt.now(tz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f%z'),
                #'host': name_list[0], #Removing to avoid double host entries on events
                'object': name_list[1],
                'counter': name_list[2],
                'value': int(value),
                'cstatus': int(cstatus)
            }
            json_output.append(counter_dict)
        self.helper.log_debug(f'JSON output result:\n{json_output}')
        return json_output
