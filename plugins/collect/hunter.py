# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "name": "Hunter",
        "description": "hunter查询",
        "references": ["https://api.hunter.io"],
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url='https://api.hunter.io/v2/domain-search',
            params={'domain': self.target.value, 'api_key': self.config.hunter.key}
        )
        if r.status_code == 200:
            result = [{'email': _['value'], 'type': _['type']} for _ in r.json()['data']['emails']]
            if len(result) != 0:
                return {
                    'EmailList': result
                }
