# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "name": "whoisxmlapi",
        "description": "whoisxmlapi查询",
        "references": ["https://subdomains.whoisxmlapi.com"],
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url='https://subdomains.whoisxmlapi.com/api/v1',
            params={'apiKey': self.config.whoisxmlapi.key, 'domainName': self.target.value}
        )
        if r.status_code == 200:
            data = r.json()
            return {
                'Subdomain': [{'subdomain': _['domain']} for _ in data['result']['records']]
            }
