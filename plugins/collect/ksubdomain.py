# -*-* coding:UTF-8
import os
import aiodns


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "枚举子域名",
        "datetime": "2022-01-01"
    }

    def domain(self):
        with self.async_pool(max_workers=self.target.setting.asyncio, threshold=self.threshold) as execute:
            for prefix in self.load_file(self.target.setting.dictionary or os.path.join("data", "subdomain.dict")):
                execute.submit(self.task, f'{prefix}.{self.target.value}')
            return {'SubdomainList': execute.result()}

    async def task(self, subdomain):
        self.log.debug(f'enum: {subdomain}')
        resolver = aiodns.DNSResolver(timeout=1)
        # resolver0.nameservers = ['114.114.114.114']
        await resolver.query(subdomain, 'A')
        return {'subdomain': subdomain}
