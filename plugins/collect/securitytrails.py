# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["https://api.securitytrails.com"],
        "description": "securitytrails查询",
        "datetime": "2022-01-09"
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url=f"https://api.securitytrails.com/v1/domain/{self.target.value}/subdomains",
            params={'apikey': self.target.setting.key}
        )
        if r.status_code in [403, 429]:
            raise Exception('Invalid API Key')
        elif r.status_code == 200:
            return {
                'SubdomainList': [{'subdomain': _} for _ in map(lambda x: x + '.' + self.target.value, r.json()['subdomains'])]
            }
