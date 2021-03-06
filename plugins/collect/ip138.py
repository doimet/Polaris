# -*-* coding:UTF-8
import lxml.etree


class Plugin(Base):
    __info__ = {
        "name": "IP138",
        "description": "IP138查询",
        "references": ["https://site.ip138.com"],
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url=f'https://site.ip138.com/{self.target.value}/domain.htm'
        )
        if r.status_code == 200:
            dom = lxml.etree.HTML(r.content)
            result = dom.xpath('//div[@class="panel"]/p[position()>1]/a/text()')
            return {
                'SubdomainList': [{'subdomain': _} for _ in result if _ != '更多子域名']
            }
