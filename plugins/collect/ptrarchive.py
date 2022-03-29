# -*-* coding:UTF-8
import re


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["http://ptrarchive.com"],
        "description": "ptrarchive查询",
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url='http://ptrarchive.com/tools/search4.htm',
            params={'label': self.target.value, 'date': 'ALL'}
        )
        if r.status_code == 200:
            result = re.findall(rf'[\w.-]+\.{self.target.value}', r.text, re.A)
            if result:
                return {
                    'SubdomainList': [{'subdomain': _} for _ in result if 'your_program_forgot_to_send_a_nonce' not in _]
                }
