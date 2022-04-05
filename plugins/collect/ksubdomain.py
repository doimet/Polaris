# -*-* coding:UTF-8
import os
import aiodns


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "name": "枚举子域名",
        "references": ["-"],
        "description": "利用DNS解析快速枚举子域名",
    }

    def domain(self):
        with self.async_pool() as execute:
            with open(os.path.join('data', 'subdomain.dict'), encoding='utf-8') as f:
                for line in f:
                    prefix = line.strip()
                    execute.submit(self.custom_task, f'{prefix}.{self.target.value}') if prefix else None
            return {'SubdomainList': execute.result()}

    async def custom_task(self, subdomain):
        self.log.debug(f'enum: {subdomain}')
        resolver = aiodns.DNSResolver(timeout=1)
        # resolver0.nameservers = ['114.114.114.114']
        await resolver.query(subdomain, 'A')
        return {'subdomain': subdomain}
