# -*-* coding:UTF-8
import re


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "robots",
        "datetime": "2022-01-01"
    }

    def domain(self) -> dict:
        with self.async_pool(max_workers=self.target.setting.asyncio, threshold=self.threshold) as execute:
            for url in [
                f'http://{self.target.value}/robots.txt',
                f'http://www.{self.target.value}/robots.txt',
            ]:
                execute.submit(self.task, url)
            return {'SubdomainList': execute.result()}

    async def task(self, url):
        r = await self.async_http(method='get', url=url)
        if r.status_code == 200:
            result = re.findall(rf'[\w.-]+\.{self.target.value}', r.text, re.A)
            if len(result) != 0:
                return [{'subdomain': _} for _ in result]
