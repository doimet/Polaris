# -*-* coding:UTF-8
import re


class Plugin(Base):
    __info__ = {
        "name": "Circl",
        "description": "circl查询",
        "references": ["https://www.circl.lu"],
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url=f'https://www.circl.lu/pdns/query/{self.target.value}',
            auth=(self.config.circl.user, self.config.circl.pwd)
        )
        if r.status_code == 401:
            raise Exception('Invalid API Key')
        elif r.status_code == 200:
            result = re.findall(rf'[\w.-]+\.{self.target.value}', r.text, re.A)
            return {
                'SubdomainList': [{'subdomain': _} for _ in result]
            }
