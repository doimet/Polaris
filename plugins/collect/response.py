# -*-* coding:UTF-8
import re


class Plugin(Base):
    __info__ = {
        "name": "response",
        "description": "response提取子域名",
        "references": ["-"],
    }

    def domain(self) -> dict:
        with self.async_pool() as execute:
            for url in [
                f'http://{self.target.value}',
                f'http://www.{self.target.value}',
            ]:
                execute.submit(self.custom_task, url)
            return {'SubdomainList': execute.result()}

    async def custom_task(self, url):
        r = await self.async_http(method='get', url=url)
        if r.status_code == 200:
            result = []
            if 'Content-Security-Policy' in r.headers.keys():
                scp_txt = r.headers['Content-Security-Policy']
                result = re.findall(rf'[\w.-]+\.{self.target.value}', scp_txt)
            if 'Access-Control-Allow-Origin' in r.headers.keys():
                scp_txt = r.headers['Access-Control-Allow-Origin']
                result1 = re.findall(rf'[\w.-]+\.{self.target.value}', scp_txt)
                result += result1
            if len(result) != 0:
                return [{'subdomain': _} for _ in result]
