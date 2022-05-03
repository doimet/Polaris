# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "name": "bufferover",
        "description": "bufferover查询",
        "references": ["https://dns.bufferover.run"],
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url=f'https://dns.bufferover.run/dns',
            params={'q': self.target.value}
        )
        if r.status_code == 200:
            response = r.json()['FDNS_A']
            data = []
            for i in response:
                ip, subdomain = i.split(',')
                data.append({'subdomain': subdomain, 'ip': ip})
            return {'SubdomainList': data}
