# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "name": "Securitytrails",
        "description": "securitytrails查询",
        "references": ["https://api.securitytrails.com"],
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url=f"https://api.securitytrails.com/v1/domain/{self.target.value}/subdomains",
            params={'apikey': self.config.securitytrails.key}
        )
        if r.status_code in [403, 429]:
            raise Exception('Invalid api key')
        elif r.status_code == 200:
            return {
                'SubdomainList': [
                    {'subdomain': _} for _ in map(lambda x: x + '.' + self.target.value, r.json()['subdomains'])
                ]
            }
