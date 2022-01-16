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

    @cli.options('path', desc="指定子域名字典", default=os.path.join('data', 'subdomain.dict'))
    @cli.options('workers', desc="协程并发数量", type=int, default=50)
    def domain(self, path, workers):
        with self.async_pool(max_workers=workers, threshold=self.threshold) as execute:
            with open(path, encoding='utf-8') as f:
                for prefix in f:
                    if prefix:
                        execute.submit(self.custom_task, f'{prefix.strip()}.{self.target.value}')
            return {'SubdomainList': execute.result()}

    async def custom_task(self, subdomain):
        self.log.debug(f'enum: {subdomain}')
        resolver = aiodns.DNSResolver(timeout=1)
        # resolver0.nameservers = ['114.114.114.114']
        await resolver.query(subdomain, 'A')
        return {'subdomain': subdomain}
