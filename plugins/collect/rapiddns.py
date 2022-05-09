# -*-* coding:UTF-8
import lxml.etree


class Plugin(Base):
    __info__ = {
        "name": "Rapiddns",
        "description": "rapiddns查询",
        "references": ["https://rapiddns.io"],
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url=f'https://rapiddns.io/subdomain/{self.target.value}',
            params={'full': 1}
        )
        if r.status_code == 200:
            dom = lxml.etree.HTML(r.content)
            selector = dom.xpath('//table[@id="table"]//tbody//tr')
            result = []
            for i in selector:
                one = i.xpath('td//text()')
                if one[3] == 'A':
                    result.append({'subdomain': one[0], 'ip': one[1], 'type': 'A'})
                else:
                    result.append({'subdomain': one[0], 'record': one[1], 'type': one[3]})
            return {
                "SubdomainList": result
            }

    def ip(self) -> dict:
        r = self.request(
            method='get',
            url=f'https://rapiddns.io/sameip/{self.target.value}',
            params={'full': 1}
        )
        if r.status_code == 200:
            dom = lxml.etree.HTML(r.content)
            selector = dom.xpath('//table[@id="table"]//tbody//tr')
            result = []
            for i in selector:
                one = i.xpath('td//text()')
                result.append({'subdomain': one[0], 'type': one[2]})
            return {
                "SubdomainList": result
            }
