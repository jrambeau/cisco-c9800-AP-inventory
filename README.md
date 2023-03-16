# AP Inventory for Cisco C9800 WLAN Controllers

Version: v002
Date: 24 mar 2023  

## Prerequisites

Install required Python Libraries:
```python
pip install -r requirements.txt
```

On the 9800 controller, enable the RESTCONF feature:
```
configure terminal
    aaa authorization exec default local 
    ip http secure-server
        restconf
```

## Run the script

```python
python inventory_c9800_ap.py
```

You will be prompted for username and password.