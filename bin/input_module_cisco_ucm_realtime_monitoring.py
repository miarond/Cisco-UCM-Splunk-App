
# encoding = utf-8
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

import json
import urllib3

def validate_input(helper, definition):
    """
    Perform basic validation checks to ensure that the lxml package is installed
    and that user input data is present and formatted correctly.
    """
    # Test if lxml package is installed
    from lxml import etree

    cucm_ip_or_hostname = definition.parameters.get('cucm_ip_or_hostname', None)
    if cucm_ip_or_hostname == None or type(cucm_ip_or_hostname) != str:
        helper.log_debug(f"Value of cucm_ip_or_hostname is {cucm_ip_or_hostname} and data type is {type(cucm_ip_or_hostname)}")
        raise ValueError("Cisco UCM IP Address or Hostname input is either missing or an incorrect data type.")
    # verify_ssl_certificate = definition.parameters.get('verify_ssl_certificate', None)
    cucm_api_account = definition.parameters.get('cucm_api_account', None)
    if cucm_api_account == None:
        raise ValueError("Cisco UCM account value is missing")
    list_of_perfmon_counters = definition.parameters.get('list_of_perfmon_counters', None)
    if list_of_perfmon_counters == None or type(list_of_perfmon_counters) != str:
        helper.log_debug(f"Value of list_of_perfmon_counters is {list_of_perfmon_counters} and data type is {type(list_of_perfmon_counters)}")
        raise ValueError("The list of Performance Monitor Counters input is either missing or an incorrect data type.")
    for counter in list_of_perfmon_counters.split(","):
        if "\\" not in counter:
            helper.log_debug(f"Value of counter is {counter}")
            raise ValueError(f"The Performance Monitor counter input value {counter} is missing backslash (\) characters.")

def collect_events(helper, ew):
    """
    Collect Performance Monitoring counter data from a Cisco Unified Communication Manager
    server, via the SOAP-based PerfMon API.  The following steps are taken:

    1. Import PerfmonServiceSession class from soap_session.py
    2. Instantiate the class, which initiates parsing of XML payloads from xml_docs.py, parses
    user-supplied counter names into a List, connects to the PerfMon API and authenticates, 
    and obtains a Session ID (Handle)
    3. Add user-specified counters to the PerfMon session
    4. Retrieve the counter values from the PerfMon session
    5. Close the PerfMon session
    6. Parse the XML counter data and convert it to JSON format
    7. Build and write an Event to the Splunk index
    """
    from soap_session import PerfmonServiceSession
    if not helper.get_arg('verify_ssl_certificate'):
        # Disable SSL Insecure Request warning messages
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Instantiate Class, open API session, parse XML and list of counters
    session = PerfmonServiceSession(helper)

    # Add counters to session
    add_result = session.add_counters()

    # Collect counter results
    counter_data_result = session.collect_counters()

    # Close session
    close_result = session.close_session()

    # Parse counter results
    counter_data = session.parse_xml_to_json(counter_data_result.content)

    # Build and write event
    event = helper.new_event(source=helper.get_input_type(), host=helper.get_arg('cucm_ip_or_hostname'), index=helper.get_output_index(), sourcetype=helper.get_sourcetype(), data=json.dumps(counter_data))
    ew.write_event(event)
