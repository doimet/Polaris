# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["https://subdomains.whoisxmlapi.com"],
        "description": "whoisxmlapi查询",
        "datetime": "2022-01-09"
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url='https://subdomains.whoisxmlapi.com/api/v1',
            params={'apiKey': self.target.setting.key, 'domainName': self.target.value}
        )
        if r.status_code == 200:
            data = r.json()
            return {
                'Subdomain': [{'subdomain': _['domain']} for _ in data['result']['records']]
            }
