# -*-* coding:UTF-8
import socket
import ssl
import asn1crypto.x509


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "通过SSL证书获取子域名",
        "datetime": "2021-12-27"
    }

    def ip(self) -> dict:
        with socket.socket() as sock:
            sock.settimeout(5)
            with ssl.wrap_socket(sock) as c:
                c.connect((self.target.value, 443))
                data = c.getpeercert(True)
        x509 = asn1crypto.x509.Certificate.load(data)
        return {
            'SubdomainList': [{'subdomain': i} for i in x509.valid_domains]
        }
