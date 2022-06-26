## API接口
### 列出列表

+ 请求url

  `api/node`

+ 请求方式

  `Method: GET`

+ 请求参数

  | 请求参数 | 参数类型 | 参数说明 |
  | ------- | ------- | ------- |
  | command | string | 执行命令 |
  | plugins | string | 插件列表 |

+ 返回参数

  | 返回参数 | 参数类型 | 参数说明 |
  | ------- | ------- | ------ |
  | code | int | 状态代码 |
  | message | string  | 提示消息 |
  | data | list    | 返回数据 |

+ 返回示例

  ```json
  
  ```

### 执行任务

+ 请求url

  `api/node`

+ 请求方式

  `Method: POST`

+ 请求参数

  | 请求参数 | 参数类型 | 参数说明 |
  | ------- | ------- | ------- |
  | command | string | 执行命令 |
  | plugins | string | 插件列表 |
  | input | list | 输入目标 |

+ 返回参数

| 返回参数 | 参数类型 | 参数说明 |
| ------- | ------- | ------- |
| data | list    | 返回数据 |
| logs | string    | 运行日志 |

+ 返回示例

  ```json
  ```