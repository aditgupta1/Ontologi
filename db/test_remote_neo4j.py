from py2neo import Graph

public_ip = '192.168.0.109'
# public_ip = '127.0.0.1'
graph = Graph(f'bolt://{public_ip}:7687/', password='pswd')

# try:
print(graph.run("MATCH (n) RETURN n LIMIT 1").data())
print('ok')
# except Exception:
#     print('not ok')


# SSID:	TP-Link_9DB6_GONG
# Protocol:	Wi-Fi 4 (802.11n)
# Security type:	WPA2-Personal
# Network band:	2.4 GHz
# Network channel:	3
# Link-local IPv6 address:	fe80::f94b:8970:1dc4:c358%9
# IPv4 address:	
# IPv4 DNS servers:	192.168.0.1
# Manufacturer:	Intel Corporation
# Description:	Intel(R) Dual Band Wireless-AC 3168
# Driver version:	19.51.23.1
# Physical address (MAC):	D4-3B-04-B8-22-61
