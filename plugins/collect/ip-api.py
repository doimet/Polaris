# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["http://ip-api.com"],
        "description": "获取网站的物理地址",
        "datetime": "2021-12-27"
    }

    def ip(self) -> dict:
        r = self.request(
            method='get',
            url=f"http://ip-api.com/json/{self.target.value}",
            params={'fields': '66842623', 'lang': 'en'}
        )
        if r.status_code == 200:
            result = r.json()
            if result['status'] == 'success':
                return {
                    'IpInfo': {
                        'address': result['country'] + (f', {result["regionName"]}' if result['regionName'] else ' ') + (
                            f', {result["city"]}' if result['city'] else ''),
                        'isp': result['isp'],
                        'org': result['org'],
                        'asn': result['as'].split(' ')[0][2:]
                    }
                }
