# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["https://www.virustotal.com"],
        "description": "virustotal查询",
        "datetime": "2022-01-06"
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url='https://www.virustotal.com/vtapi/v2/domain/report',
            params={'apikey': self.config.virustotal.key, 'domain': self.target.value},
            headers={'x-apikey': self.config.virustotal.key}
        )
        if r.status_code == 200:
            resp = r.json()
            return {
                'SubdomainList': [{'subdomain': _} for _ in resp['subdomains']],
            }
