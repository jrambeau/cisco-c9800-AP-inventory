"""
This file implements the C9800 class.

"""
from re import A
import requests
import urllib3
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from netaddr import EUI, mac_unix_expanded
import logging


class C9800:
    def __init__(self, ip, user, password):
        self.controller_ip = ip
        self.controller_user = user
        self.controller_password = password
        self.controller_auth = HTTPBasicAuth(user, password)
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.ap_list = {}
        self.headers = {
            'Accept': "application/yang-data+json",
            'Content-Type': "application/yang-data+json",
            'cache-control': "no-cache"
        }
        self.baseurl = f"https://{self.controller_ip}/restconf/data/"


    def __execute_REST(self, method, resource, payload=None):
        logging.info(f"Executing method {method} on resource {resource} on controller {self.controller_ip}")
        url = self.baseurl + resource
        response = None
        try:
            response = requests.request(method,
                    url,
                    headers=self.headers,
                    verify=False,
                    auth=self.controller_auth,
                    json=payload)
            response.raise_for_status()
        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')
        except Exception as err:
            logging.exception(f'Other error occurred: {err}')
        else:
            logging.info(f"Success!")
        return response


    def get_joined_aps(self):
        resource_capwap = "Cisco-IOS-XE-wireless-access-point-oper:access-point-oper-data/capwap-data"
        response_capwap = self.__execute_REST(method="GET", resource=resource_capwap)
        resource_radio = "Cisco-IOS-XE-wireless-access-point-oper:access-point-oper-data/radio-oper-data"
        response_radio = self.__execute_REST(method="GET", resource=resource_radio)
        resource_cdp = "Cisco-IOS-XE-wireless-access-point-oper:access-point-oper-data/cdp-cache-data"
        response_cdp = self.__execute_REST(method="GET", resource=resource_cdp)
        resource_lldp = "Cisco-IOS-XE-wireless-access-point-oper:access-point-oper-data/lldp-neigh"
        response_lldp = self.__execute_REST(method="GET", resource=resource_lldp)



        try:
            json_payload_capwap = response_capwap.json()
            capwap_data = json_payload_capwap['Cisco-IOS-XE-wireless-access-point-oper:capwap-data']

            json_payload_radio = response_radio.json()
            radio_oper_data = json_payload_radio['Cisco-IOS-XE-wireless-access-point-oper:radio-oper-data']

            json_payload_cdp = response_cdp.json()
            cdp_data = json_payload_cdp['Cisco-IOS-XE-wireless-access-point-oper:cdp-cache-data']

            json_payload_lldp = response_lldp.json()
            lldp_data = json_payload_lldp['Cisco-IOS-XE-wireless-access-point-oper:lldp-neigh']


            # Going through each Access Point
            for x, entry in enumerate(capwap_data):
                radio_list = {} # Reset radio_list for each new AP
                lldp_list = {} # Reset lldp_list for each new AP

                hostname = entry["name"]
                ipaddr = entry["ip-addr"]
                ethernet_mac = entry["device-detail"]["static-info"]["board-data"]["wtp-enet-mac"]
                serial = entry["device-detail"]["static-info"]["board-data"]["wtp-serial-num"]
                macwireless = entry["wtp-mac"]
                apmodel = entry["device-detail"]["static-info"]["ap-models"]["model"]
                tagpolicy = entry["tag-info"]["policy-tag-info"]["policy-tag-name"]
                tagsite = entry["tag-info"]["site-tag"]["site-tag-name"]
                tagrf = entry["tag-info"]["rf-tag"]["rf-tag-name"]
                cc = entry["country-code"]
                MACwireless = EUI(macwireless, dialect=mac_unix_expanded)
                MACeth = EUI(ethernet_mac, dialect=mac_unix_expanded)

                # Write global information on the AP
                self.ap_list[x] = {
                    "Hostname":hostname,
                    "Model":apmodel,
                    "Serial":serial,
                    "IP_Address":ipaddr,
                    "MAC_eth":str(MACeth),
                    "MAC_wireless":str(MACwireless),
                    "Policy_Tag":tagpolicy,
                    "Site_Tag":tagsite,
                    "RF_Tag":tagrf,
                    "Country_Code":cc
                }

                # LLDP information
                for lldp in lldp_data:
                    if lldp["wtp-mac"] == macwireless:
                        try: lldp_list.update({"LLDP_Neighbor":lldp["system-name"]})
                        except: lldp_list.update({"LLDP_Neighbor":""})
                        try: lldp_list.update({"LLDP_Neighbor_IP":lldp["mgmt-addr"]})
                        except: lldp_list.update({"LLDP_Neighbor_IP":""})
                        try: lldp_list.update({"LLDP_Neighbor_Interface":lldp["port-description"]})
                        except: lldp_list.update({"LLDP_Neighbor_Interface":""})
                # Write LLDP information
                self.ap_list[x].update(lldp_list)

                num_radio_slots = entry["device-detail"]["static-info"]["num-slots"]    # Cisco APs can have 2, 3, 4 radios

                # Radios information
                for radio in radio_oper_data:
                    for y in range(num_radio_slots):
                        if radio["wtp-mac"] == macwireless:
                            if radio["radio-slot-id"] == y:
                                    radio_list.update({
                                        "radio"+str(y)+"_Type":radio["radio-type"],
                                        "radio"+str(y)+"_Adminstate":radio["admin-state"],
                                        "radio"+str(y)+"_Operstate":radio["oper-state"],
                                        "radio"+str(y)+"_Channel":radio["phy-ht-cfg"]["cfg-data"]["curr-freq"],
                                        "radio"+str(y)+"_Channelwidth":radio["phy-ht-cfg"]["cfg-data"]["chan-width"],
                                        "radio"+str(y)+"_TxpowerLevel":radio["radio-band-info"][0]["phy-tx-pwr-cfg"]["cfg-data"]["current-tx-power-level"],
                                        "radio"+str(y)+"_dBm":radio["radio-band-info"][0]["phy-tx-pwr-lvl-cfg"]["cfg-data"]["curr-tx-power-in-dbm"]
                                    })
                # Write radios information
                self.ap_list[x].update(radio_list)

        except ValueError as err:
            logging.info(f"No data was returned")
        except Exception as err:
            logging.exception(f"Other error: {err}")
        else:
            logging.info(f"Success! {len(self.ap_list)} APs joined")

        return self.ap_list


    def get_site_tags(self):
        resource = "Cisco-IOS-XE-wireless-site-cfg:site-cfg-data/site-tag-configs/site-tag-config"

        result = self.__execute_REST(method="GET", resource=resource)
        data = result.json()
        logging.info(f"The list of tags is: {data}")
        return data


    def set_site_tag(self, ap_tag):
        logging.info(f"Creating the site tag {ap_tag}")

        resource = "Cisco-IOS-XE-wireless-site-cfg:site-cfg-data/site-tag-configs/site-tag-config"

        data = {'Cisco-IOS-XE-wireless-site-cfg:site-tag-config': [
                {'site-tag-name': ap_tag, 'is-local-site': False}
                ]
        }
        self.__execute_REST(method="PATCH", resource=resource, payload=data)


    def set_ap_tag(self, ap_mac, ap_tag):
        logging.info(f"Changing AP MAC {ap_mac} to have tag {ap_tag}")

        payload = {"ap-tag": 
            {"ap-mac":ap_mac, 
            "site-tag":ap_tag}
        }
        resource = "/Cisco-IOS-XE-wireless-ap-cfg:ap-cfg-data/ap-tags/ap-tag/"
        response = self.__execute_REST(method="PATCH", resource=resource, payload=payload)
        return response
