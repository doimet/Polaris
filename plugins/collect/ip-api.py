# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "name": "IP-API",
        "description": "获取网站的物理地址",
        "references": ["http://ip-api.com"],
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
                    'IPInfo': {
                        'address': result['country'] + (f', {result["regionName"]}' if result['regionName'] else ' ') + (
                            f', {result["city"]}' if result['city'] else ''),
                        'isp': result['isp'],
                        'org': result['org'],
                        'asn': result['as'].split(' ')[0][2:]
                    }
                }
