# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "name": "ensys",
        "description": "censys查询",
        "references": ["https://www.censys.io"],
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
                auth=(self.config.censys.api_id, self.config.censys.secret)
            )
            if r.status_code == 403:
                raise Exception('Invalid API Key')
            elif r.status_code == 200:
                content = r.json()
                if content['error']:
                    raise Exception('Invalid API Key')
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
