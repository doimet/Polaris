# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "name": "IP-info",
        "description": "通过ipinfo获取信息",
        "references": ["http://ipinfo.io"],
    }

    def ip(self) -> dict:
        r = self.request(
            method='get',
            url=f'http://ipinfo.io/{self.target.value}',
            params={'token': self.config.ipinfo.key},

        )
        if not self.config.ipinfo.key or r.status_code == 403:
            raise Exception('Invalid api key')
        if r.status_code == 200:
            response = r.json()
            return {
                'IPInfo': {
                    "国家": response['country'],
                    "城市": response['city'],
                    "地区": response['region'],
                    "所属组织": response['org'],
                }
            }
