# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["https://api.hunter.io"],
        "description": "hunter查询",
        "datetime": "2022-01-06"
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url='https://api.hunter.io/v2/domain-search',
            params={'domain': self.target.value, 'api_key': self.target.setting.key}
        )
        if r.status_code == 200:
            result = [{'email': _['value'], 'type': _['type']} for _ in r.json()['data']['emails']]
            if len(result) != 0:
                return {
                    'EmailList': result
                }
