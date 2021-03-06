# -*-* coding:UTF-8
import base64


class Plugin(Base):
    __info__ = {
        "name": "FoFa",
        "description": "FoFa查询",
        "references": ["https://fofa.info"],
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url='http://fofa.info/api/v1/search/all',
            params={
                'email': self.config.fofa.auth.email,
                'key': self.config.fofa.auth.key,
                'page': 1,
                'qbase64': base64.b64encode(f'domain="{self.target.value}"'.encode()).decode(),
                'full': 'false',
                'fields': "ip,host",
                'size': 10000,
            }
        )
        if r.status_code == 200:
            resp = r.json()
            if not resp['error']:
                return {
                    'SubdomainList': [
                        {
                            'subdomain': _[1].replace('https://', '').replace('http://', ''),
                            'ip': _[0],
                        } for _ in resp['results'] if self.target.value in _[1]
                    ]
                }
