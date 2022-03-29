import socket
import ssl


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "通过SSL证书提取子域名",
    }

    def domain(self) -> dict:
        ctx = ssl.create_default_context()
        s = ctx.wrap_socket(socket.socket(), server_hostname=self.target.value)
        s.connect((self.target.value, 443))
        cert_dict = s.getpeercert()
        result = [_[1] for _ in cert_dict['subjectAltName']]
        return {
            'SubdomainList': [{'subdomain': _} for _ in result if _ not in [self.target.value, '*.' + self.target.value]]
        }
