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

    @cli.options('domain', desc="设置输入目标", default='{self.target.value}')
    @cli.options('path', desc="子域名字典路径", default=os.path.join('data', 'subdomain.dict'))
    @cli.options('workers', desc="协程并发数量", type=int, default=50)
    def domain(self, domain, path, workers):
        with self.async_pool(max_workers=workers) as execute:
            with open(path, encoding='utf-8') as f:
                for line in f:
                    prefix = line.strip()
                    execute.submit(self.custom_task, f'{prefix}.{domain}') if prefix else None
            return {'SubdomainList': execute.result()}

    async def custom_task(self, subdomain):
        self.log.debug(f'enum: {subdomain}')
        resolver = aiodns.DNSResolver(timeout=1)
        # resolver0.nameservers = ['114.114.114.114']
        await resolver.query(subdomain, 'A')
        return {'subdomain': subdomain}
