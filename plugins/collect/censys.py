# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["https://www.censys.io"],
        "description": "censys查询",
        "datetime": "2022-01-06"
    }

    def domain(self) -> dict:
        page, pages, result = 1, 1, []
        while page <= pages:
            data = {
                'query': f'parsed.names: {self.target.value}',
                'page': page,
                'fields': ['parsed.names'],
                'flatten': True
            }
            r = self.request(
                method='post',
                url='https://www.censys.io/api/v1/search/certificates',
                json=data,
                auth=(self.target.setting.api_id, self.target.setting.secret)
            )
            if r.status_code == 403:
                raise Exception('Invalid API Key')
            elif r.status_code == 200:
                content = r.json()
                for i in content['results']:
                    for j in i['parsed.names']:
                        result.append(j)
                pages = content['metadata']['pages']
                page += 1
            else:
                break
        return {
            'SubdomainList': [{'subdomain': _} for _ in result]
        }
