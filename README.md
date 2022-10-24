# AP Inventory for Cisco C9800 WLAN Controllers

Version: v001  
Date: 24 oct 2022  

## Prerequisites

Python Libraries:
```python
pip install pandas
pip install openpyxl
```

On the 9800 controller, enable the RESTCONF feature:
```
configure terminal
    ip http secure-server
        restconf
```

## Run the script

```python
python inventory_c9800_ap.py -user <user> -password <password> -wlc_ip <controller IP>