# -*-* coding:UTF-8
import re


class Plugin(Base):
    __info__ = {
        "name": "robots",
        "description": "robots查询",
        "references": ["-"],
    }

    def domain(self) -> dict:
        with self.async_pool() as execute:
            for url in [
                f'http://{self.target.value}/robots.txt',
                f'http://www.{self.target.value}/robots.txt',
            ]:
                execute.submit(self.custom_task, url)
            return {'SubdomainList': execute.result()}

    async def custom_task(self, url):
        r = await self.async_http(method='get', url=url)
        if r.status_code == 200:
            result = re.findall(rf'[\w.-]+\.{self.target.value}', r.text, re.A)
            if len(result) != 0:
                return [{'subdomain': _} for _ in result]
