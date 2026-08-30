# AutoDL 应用实例 API

官方：<https://autodl.art/docs/app_api/>  
HOST：`https://www.autodl.art`  
前缀：`/api/v1/adl_dev/dev/instance/pro`

鉴权：`Authorization: <开发者Token>`，不要 `Bearer`。Token 在 autodl.com 控制台 → 账号 → 设置 → 开发者 Token。同类 Pro 接口通常要实名。

成功：`code == "Success"`。

## 接口

| 动作 | 方法 | 路径 | 参数 |
|---|---|---|---|
| 列表 | POST | `/list` | JSON `page_index` `page_size` |
| 状态 | GET | `/status?instance_uuid=` | **query**，不要 JSON body |
| 详情 | GET | `/snapshot?instance_uuid=` | **query** |
| 开机 | POST | `/power_on` | JSON `instance_uuid` + `payload":"gpu"` |
| 关机 | POST | `/power_off` | JSON `instance_uuid` |
| 释放 | POST | `/release` | 销毁。本技能禁止调用 |

文档里 GET 写成 JSON body 是错的，实测 `RequestParameterIsWrong`。

开机已 running：`BadRequest`「当前实例状态无法进行开机操作」。脚本把它当成已开机。

`power_on` 的 Success 只表示指令已下发。要轮询到 `running`。关机后会经过 `shutting_down` 再到 `shutdown`。

## snapshot 常用字段

| 字段 | 用途 |
|---|---|
| `proxy_host` | SSH 主机，如 `connect.westd.seetacloud.com` |
| `ssh_port` | SSH 端口，每次开机可能变 |
| `root_password` | SSH 密码。禁止打印 |
| `ssh_command` | 完整 ssh 命令 |
| `service_6006_domain` | WebUI-6006 映射。面板以机器上 `/root/面板地址.txt` 为准（可能是 `uu…` 而不是 `u…`） |
| `jupyter_domain` | Jupyter |
| `cg_application_info.application_name` | 应用名 |

## 和容器实例的区别

| 产品 | HOST | 路径 |
|---|---|---|
| **应用实例（本技能）** | `www.autodl.art` | `/api/v1/adl_dev/dev/instance/pro` |
| 容器实例 Pro | `api.autodl.com` | `/api/v1/dev/instance/pro` |
| 普通容器 | 无官方开发者开关机 | 不要用 |

UUID 都是 `pro-…`，打错 HOST 会空列表或无权限。

## Comfy 就绪

`GET $SEETACLOUD_BASE_URL/api/comfy/status` → `reason=ready`  
`GET …/api/comfy/queue-status` 不要 `unreachable`；挂了先 `POST /api/comfy/stop` 再 `start`。
