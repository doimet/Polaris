# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "name": "Virustotal",
        "description": "virustotal查询",
        "references": ["https://www.virustotal.com"],
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
