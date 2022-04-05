# 插件编写
## 内置对象
+ `target`: 
  + `target.key`: 用于获取输入类型
  + `target.value`: 用于获取输入目标
+ `config`: 用于获取配置参数
+ `log`: 
  + `log.debug`: 用于输出调式信息
  + `log.info`: 用于输出普通信息
  + `log.success`: 用于输出成功信息
  + `log.failure`: 用于输出失败信息
  + `log.warn`: 用于输出警告信息
  + `log.error`: 用于输出错误信息
+ `async_pool`: 用于创建异步连接池(上下文管理)
  ```
  async_pool(max_workers: int) -> Object
  传入并发数量, 默认50(实际数值需参考配置文件)
  返回执行对象, 对象可调用如下方法:
  submit: 用于提交任务, 需传入任务函数、任务参数
  result: 用于获取返回结果
  ```
+ `echo_query`: 针对命令无回显时调用(上下文管理)
  ```
  echo_query() -> Object
  返回查询对象, 对象可调用如下方法:
  get_url: 用于获取url
  get_subdomain: 用于获取子域名
  verify: 用于请求验证 True or False
  result: 用于获取返回结果
  ```
  
## 内置方法

+ `request`: 网络请求方法
  ```
  request(method: str, url: str, path: str, **kwargs) -> Response
  传入请求参数
  返回响应对象
  ```
+ `async_http`: 异步网络请求方法
  ```
  await self.async_http(method: str, url: str, path: str, **kwargs) -> Response
  传入请求参数
  返回响应对象
  ```
+ `build_md5_str`/`MD5`: 计算字符串MD5
  ```
  build_md5_str(source: str) -> str
  传入源字符串
  返回加密字符串
  ```
+ `build_random_int`/`randomInt`: 生成随机整数
  ```
  build_random_int(length: int) -> int
  传入生成长度
  返回随机整数
  ```
+ `build_random_str`/`randomStr`: 生成随机字符串
  ```
  build_random_str(length: int) -> str
  传入生成长度
  返回随机字符串
  ```
+ `build_random_lower_str`/`randomLowercase`: 生成随机小写字符串
  ```
  build_random_lower_str(length: int) -> str
  传入生成长度
  返回随机小写字符串
  ```
+ `build_random_upper_str`/`randomUppercase`: 生成随机大写字符串
  ```
  build_random_upper_str(length: int) -> str
  传入生成长度
  返回随机大写字符串
  ```
+ `base64_encode`/`base64Encode`: Base64编码字符串
  ```
  base64_encode(source: str) -> str
  传入源字符串
  返回编码字符串
  ```
+ `base64_decode`/`base64Decode`: Base64解码字符串
  ```
  base64_decode(source: str) -> str
  传入源字符串
  返回解码字符串
  ```
+ `jsonp_to_json`: jsonp字符串转json
  ```
  jsonp_to_json(jsonp_str: str) -> dict
  传入jsonp字符串
  返回字典类型数据
  ```
+ `build_web_shell`: 生成WebShell
  ```
  build_web_shell(lang: str) -> tuple
  传入生成的脚本语言
  返回webshell代码、webshell密码、webshell验证代码
  注: 目前只支持php、asp、aspx三种语言, 后面会添加jsp
  ```
+ `is_exist_waf`: 判断Waf
  ```
  is_exist_waf(content: str) -> bool
  传入网页文本内容
  返回对waf的判断True or False
  ```
## 内置装饰器
+ `cli.params`: 类属性, 用户获取扩展参数
+ `cli.command`: 类方法装饰器, 用于自定义命令(使用--console参数调用)
  ```
  cli.command(description: str)
  description: 描述信息
  ```
+ `cli.options`: 类方法装饰器, 用户定义命令参数, 配合`cli.command`一起使用
  ```
  cli.options(parmas: str, help: str, type, required, default, choice)
  parmas: 参数名称
  help: 参数描述信息
  type: 参数值类型, 可选: str、int、float、bool
  required: 参数是否必须, bool类型
  default: 参数默认值
  choice: 参数可选值, list类型
  ```

## 插件模板
### 模板一
```python
# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "author": "作者",
        "name": "插件名称",
        "references": ["来源"],
        "description": "描述信息",
    }

    def domain(self) -> dict:
        """ 编写代码 """
        ...
```
### 模板二
```python
# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "author": "作者",
        "name": "插件名称",
        "references": ["来源"],
        "description": "描述信息",
    }

    def url(self) -> dict:
        """ 验证代码 """
        ...
    
    @cli.command(description="执行系统命令")
    @cli.options('cmd', help="执行的命令", default="whoami")
    def exec_cmd(self, cmd) -> dict:
        """ 利用代码 """
        ...

```

## 注意事项
1. 插件内定义的方法名称并非固定的, 而是根据这个插件所接受的输入类型来以此命名的
