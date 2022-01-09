# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["https://otx.alienvault.com"],
        "description": "alienvault查询",
        "datetime": "2022-01-09"
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url=f'https://otx.alienvault.com/api/v1/indicators/domain/{self.target.value}/passive_dns'
        )
        if r.status_code == 200:
            response = r.json()['passive_dns']
            return {
                'SubdomainList': [
                    {
                        'subdomain': _['hostname'],
                        'ip': _['address']
                    } for _ in response if f'.{self.target.value}' in _['hostname'] and 'A' in _['record_type']]
            }
