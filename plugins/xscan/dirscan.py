# -*-* coding:UTF-8
import os
import re
from simhash import Simhash
from urllib.parse import urlparse, urljoin


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "扫描网站目录",
        "datetime": "2022-02-07"
    }

    def init(self):
        self.request_times = 0

    def custom_request_test(self, url):
        r = self.request(method='get', url=urljoin(url, self.build_random_str() + '.js'))
        first_sim = Simhash(re.sub("[\r|\n|\t| ]+", " ", r.text))
        r = self.request(method='get', url=urljoin(url, self.build_random_str() + '.js'))
        second_sim = Simhash(re.sub("[\r|\n|\t| ]+", " ", r.text))
        distance = first_sim.distance(second_sim)
        flag_sim = second_sim
        return distance, flag_sim

    @cli.options('url', desc="扫描目标地址", default='{self.target.value}')
    @cli.options('extension', desc="指定后缀", choice=['asp', 'jsp', 'php', 'aspx', '*'], default='*')
    @cli.options('dict_path', desc="目录字典路径", default=os.path.join('data', 'path.dict'))
    @cli.options('timeout', desc="连接超时时间", type=int, default=3)
    @cli.options('workers', desc="协程并发数量", type=int, default='{self.config.general.asyncio}')
    def url(self, url, extension, dict_path, timeout, workers) -> dict:
        distance, flag_sim = self.custom_request_test(url)
        with open(dict_path, encoding='utf-8') as f:
            path_list = [_.strip() for _ in f]
        with self.async_pool(max_workers=workers) as execute:
            for path in path_list:
                path = path.strip().replace('%DOMAIN%', urlparse(url).netloc)
                for extend in [
                    _ for _ in ['php', 'jsp', 'asp', 'php', 'aspx'] if extension == _ or extension == '*'
                ]:
                    path = path.strip().replace('%EXT%', extend)
                    execute.submit(self.custom_task, url, timeout, distance, flag_sim, path)
            return {'网站目录信息': execute.result()}

    async def custom_task(self, url, timeout, distance, flag_sim, path):
        self.log.debug(f'start scan path: {path}')
        r = await self.async_http(method='get', url=urljoin(url, path), cache=True, timeout=timeout)
        if r.status_code in self.string_split('200-403,500-510'):
            text_sim = Simhash(re.sub("[\r|\n|\t| ]+", " ", r.text))
            if self.request_times > 15:
                raise Exception('超过15次都访问了同一页面')
            elif self.is_exist_waf(r.text):
                raise Exception('请求被WAF拦截')
            elif text_sim.distance(flag_sim) - distance > 0.3:
                r.encoding = r.apparent_encoding
                match = re.search('<title>(.*?)</title>', r.text, re.IGNORECASE)
                title = match.group(1).strip() if match else '-'
                self.log.info(f'found exist path: {path} <{r.status_code}>')
                return {
                    '相对路径': path,
                    '网页标题': title,
                    '响应大小': r.length,
                    '状态码': r.status_code
                }
            else:
                self.request_times += 1
        elif r.status_code in [512, 418]:
            raise Exception('请求被拒绝, 建议使用动态代理请求')
