# -*-* coding:UTF-8
import re


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "sitemap提取子域名",
        "datetime": "2022-01-01"
    }

    def domain(self) -> dict:
        with self.async_pool() as execute:
            for url in [
                f'http://{self.target.value}/sitemap.xml',
                f'http://{self.target.value}/sitemap.txt',
                f'http://{self.target.value}/sitemap.html',
                f'http://{self.target.value}/sitemap_index.xml',
                f'http://www.{self.target.value}/sitemap.xml',
                f'http://www.{self.target.value}/sitemap.txt',
                f'http://www.{self.target.value}/sitemap.html',
                f'http://www.{self.target.value}/sitemap_index.xml',
            ]:
                execute.submit(self.custom_task, url)
            return {'SubdomainList': execute.result()}

    async def custom_task(self, url):
        r = await self.async_http(method='get', url=url)
        if r.status_code == 200:
            result = re.findall(rf'[\w.-]+\.{self.target.value}', r.text, re.A)
            return [{'subdomain': _} for _ in result]
