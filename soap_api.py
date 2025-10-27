import requests
from xml.etree import ElementTree as ET

endpoint = "https://185.243.116.132:22704/4DSOAP/"
auth = ("WebUser", "Black-1981-Rose")
headers = {
"Content-Type": "text/xml; charset=utf-8",
"SOAPAction": "A_WebService#ws_wes_kunde_save"
}

print('endpoint: ', endpoint)
print('auth: ', auth)

kunde_xml = """<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope
xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:xsd="http://www.w3.org/2001/XMLSchema"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:tns="http://www.4d.com/namespace/default"
SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
SOAP-ENV:Body
tns:ws_wes_kunde_save
<betrieb_id xsi:type="xsd:int">1</betrieb_id>
<kunde_anrede xsi:type="xsd:string">Herr</kunde_anrede>
<kunde_vorname xsi:type="xsd:string">Alice</kunde_vorname>
<kunde_nachname xsi:type="xsd:string">Beispiel</kunde_nachname>
<kunde_firmenname xsi:type="xsd:string">Example GmbH</kunde_firmenname>
<kunde_strasse_nr xsi:type="xsd:string">Beispielweg 1</kunde_strasse_nr>
<kunde_plz xsi:type="xsd:string">12345</kunde_plz>
<kunde_ort xsi:type="xsd:string">Musterstadt</kunde_ort>
<kunde_land xsi:type="xsd:string">Deutschland</kunde_land>
<kunde_land_iso xsi:type="xsd:string">DE</kunde_land_iso>
<kunde_telefon xsi:type="xsd:string">+49 111 2222</kunde_telefon>
<kunde_email xsi:type="xsd:string">alice.beispiel@example.test</kunde_email>
<kunde_id_input xsi:type="xsd:int" xsi:nil="true"/>
<kontakt_id_input xsi:type="xsd:int" xsi:nil="true"/>
<kunde_is_disabled xsi:type="xsd:boolean">false</kunde_is_disabled>
<webshop_identification xsi:type="xsd:string">Shopify</webshop_identification>
<optional_data xsi:type="tns:ArrayOfstring" xsi:nil="true"/>
</tns:ws_wes_kunde_save>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""

print('kunde_xml: ', kunde_xml)

r = requests.post(endpoint, data=kunde_xml, headers=headers, auth=auth, timeout=30, verify=False)
print(r.status_code)
print(r.text)


try:
    ns = {'ns': 'http://www.4d.com/namespace/default'}
    root = ET.fromstring(r.text)
    kunde_id = root.find('.//{http://www.4d.com/namespace/default}kunde_id')
    if kunde_id is not None:
        print("kunde_id:", kunde_id.text)
        order_headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "A_WebService#ws_wes_order_save"
        }
        order_xml = """<SOAP-ENV:Envelope
        xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:tns="http://www.4d.com/namespace/default"
        SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
        SOAP-ENV:Body
        tns:ws_wes_order_save
        <betrieb_id xsi:type="xsd:int">1</betrieb_id>
        <kunde_id xsi:type="xsd:int">{}</kunde_id>
        <order_date xsi:type="xsd:string">2025-12-01</order_date>
        <order_total xsi:type="xsd:decimal">99.99</order_total>
        </tns:ws_wes_order_save>
        </SOAP-ENV:Body>
        </SOAP-ENV:Envelope>""".format(kunde_id.text)

        o = requests.post(endpoint, data=order_xml, headers=order_headers, auth=auth, timeout=30)
        print(o.status_code)
        print(o.text)
    else:
        print("kunde_id not found; cannot proceed with order creation.")
except Exception as e:
    print("Error parsing response:", e)