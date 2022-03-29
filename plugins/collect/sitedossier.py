# -*-* coding:UTF-8
import lxml.etree


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["http://www.sitedossier.com"],
        "description": "sitedossier查询",
    }

    def domain(self) -> dict:
        page, result = 1, []
        while True:
            r = self.request(
                method='get',
                url=f"http://www.sitedossier.com/parentdomain/{self.target.value}/{page}",
            )
            if r.status_code == 200 and 'Show next 100 items' in r.text:
                dom = lxml.etree.HTML(r.content)
                for i in dom.xpath("//dd//ol/li//a/@href"):
                    result.append(i[6:])
                page += 100
            else:
                return {
                    'SubdomainList': [{'subdomain': _} for _ in result]
                }
