# -*-* coding:UTF-8
import lxml.etree


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "name": "ICP备案查询网",
        "references": ["https://www.beianx.cn"],
        "description": "备案查询",
    }

    def icp(self) -> dict:
        return self.custom_search()

    def domain(self) -> dict:
        return self.custom_search()

    def company(self) -> dict:
        return self.custom_search()

    def custom_search(self):
        r = self.request(
            method='get',
            url=f'https://www.beianx.cn/search/{self.target.value}'
        )
        if r.status_code == 200:
            dom = lxml.etree.HTML(r.content)
            res = dom.xpath(
                (
                    '//div[@class="container"]//tbody/tr/td[2]/a/text() | '
                    '//div[@class="container"]//tbody/tr/td[4]/text() | '
                    '//div[@class="container"]//tbody/tr/td[6]//a/text() | '
                    '//div[@class="container"]//tbody/tr/td[9]/a/@href'
                )
            )
            company, icp, subdomain, info_url = [_.strip() for _ in res]
            r0 = self.request(
                method='get',
                url=f'https://www.beianx.cn{info_url}'
            )
            if r0.status_code == 200:
                dom = lxml.etree.HTML(r0.content)
                domain_list = dom.xpath('//div[@class="container"]//table[@class="table table-bordered table-beianx-details"]//tr[2]/td[2]//a//text()')
            else:
                domain_list = []
            return {
                "ICPInfo": {
                    "icp": icp,
                    "subdomain": subdomain,
                    "company": company,
                },
                "DomainList": domain_list
            }

