# AP Inventory for Cisco C9800 WLAN Controllers

Version: v001
Date: 24 oct 2022
Auteurs: Jonathan RAMBEAU @rambo_fi

## 1. Prerequisites

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