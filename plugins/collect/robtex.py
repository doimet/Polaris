# -*-* coding:UTF-8
import re


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "name": "Robtex",
        "references": ["https://www.robtex.com"],
        "description": "robtex查询",
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url=f'https://www.robtex.com/dns-lookup/{self.target.value}',
        )
        if r.status_code == 200:
            result = re.findall(rf'[\w.-]+\.{self.target.value}', r.text, re.A)
            return {
                'SubdomainList': [{'subdomain': _} for _ in result]
            }
