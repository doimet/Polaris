# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["http://ipinfo.io"],
        "description": "通过ipinfo获取信息",
        "datetime": "2021-12-27"
    }

    def ip(self) -> dict:
        r = self.request(
            method='get',
            url=f'http://ipinfo.io/{self.target.value}',
            params={'token': self.target.setting.key}
        )
        if r.status_code == 200:
            response = r.json()
            return {
                'IpInfo': {
                    "国家": response['country'],
                    "城市": response['city'],
                    "地区": response['region'],
                    "所属组织": response['org'],
                }
            }
