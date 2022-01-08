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

    @cli.options('file_path', desc="指定子域名字典", default=os.path.join('data', 'subdomain.dict'))
    def domain(self, file_path):
        with self.async_pool(max_workers=self.target.setting.asyncio, threshold=self.threshold) as execute:
            with open(file_path, encoding='utf-8') as f:
                for prefix in f:
                    if prefix:
                        execute.submit(self.task, f'{prefix.strip()}.{self.target.value}')
            return {'SubdomainList': execute.result()}

    async def task(self, subdomain):
        self.log.debug(f'enum: {subdomain}')
        resolver = aiodns.DNSResolver(timeout=1)
        # resolver0.nameservers = ['114.114.114.114']
        await resolver.query(subdomain, 'A')
        return {'subdomain': subdomain}
