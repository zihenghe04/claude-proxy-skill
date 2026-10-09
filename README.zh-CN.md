# Claude Proxy Skill

[English](README.md) · [简体中文](README.zh-CN.md)

一个可安装的 AI 技能，用于检查和优化 **Clash Verge Rev / Mihomo** 中的 Claude 分流、节点出口和 DNS 隐私。AI 会发现你的环境、生成局部方案、在本机备份，并同时验证 Claude 与日常网页访问。

项目不包含原始电脑的订阅、账号、节点、出口 IP、私人配置或诊断记录。流程面向 macOS、Windows、Linux；已观察的桌面工作流来自 macOS，其他系统需在本机发现配置并验收。不承诺防封号，不清理登录凭证或设备标识。

## 安装

需要 Git 和 Python 3.10+。Windows 可将 `python3` 改为 `py`。

```sh
git clone https://github.com/zihenghe04/claude-proxy-skill.git
cd claude-proxy-skill
python3 install.py --target codex
```

Claude Code 用户：

```sh
python3 install.py --target claude
```

支持 `~/.agents/skills` 的其他 AI 客户端：

```sh
python3 install.py --target agents
```

可用 `--dest /path/to/skills` 指定其他技能根目录。安装器不会覆盖已有技能，只复制技能文件，不修改网络。安装后重启或刷新 AI 客户端。无法访问本机的纯网页/云端 AI 会话不能操作你的本地代理。

## 让 AI 操作

在 Codex 中输入：

```text
使用 $claude-proxy-optimize 检查我现在的 Clash 配置，优化 Claude 分流和 DNS 隐私，并确认日常网站仍然可以打开。修改前先备份。
```

在 Claude Code 中输入：

```text
/claude-proxy-optimize 检查我的代理，比较适合 Claude 的节点，应用验证过的配置，同时保留日常网页访问。
```

[Claude Code 官方支持个人技能目录和斜杠调用](https://code.claude.com/docs/en/skills)。主体采用标准 SKILL.md，agents/openai.yaml 提供可选的 Codex 界面信息。其他客户端需支持本地技能并提供文件/终端或桌面控制工具；本项目不会授予权限，也不会替你安装代理客户端。

## 自动化工具

AI 可直接按技能流程操作。Python 辅助工具的在线检测需要 `curl`，YAML 检查和方案生成需要 PyYAML，建议安装到虚拟环境：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Windows 使用 `.venv\Scripts\python.exe`。下列路径相对于项目仓库；安装后，脚本在安装的技能目录内。

```sh
.venv/bin/python skills/claude-proxy-optimize/scripts/proxy_tool.py inspect --config /path/to/active.yaml
.venv/bin/python skills/claude-proxy-optimize/scripts/proxy_tool.py plan --config /path/to/active.yaml --node EXISTING_NODE --output runs/plan-01
```

检查只输出允许公开的字段摘要；仅在本机选节点时加 `--show-names`。生成方案会创建三个权限受限的本地覆写文件，不修改活动配置。AI 将条目合并到正确的持久化配置层，保留已有条目及独立的代理节点引导 DNS，再重载和验收。

```sh
.venv/bin/python skills/claude-proxy-optimize/scripts/proxy_tool.py probe --controller http://127.0.0.1:9090 --proxy http://127.0.0.1:7890 --group Claude --nodes NODE_A NODE_B
```

示例端口和节点名必须替换为本机发现的值。已有 Unix 套接字时用 `--socket /path/to/core.sock` 代替 controller。控制器密钥仅放在本机 `MIHOMO_API_SECRET` 环境变量中。比较会临时切换指定手动组，结束时恢复并验证原节点，默认输出编号及每次运行加盐的出口标识。不要并发运行；强制中断后仍需核对恢复。最终节点另由客户端选择并保存。

`--include-support` 可选加入共享监控/CDN/客服域名，可能同时影响其他软件。`--risk` 会把测得的公网出口 IP 发送给第三方 Net.Coffee，默认关闭。`--show-ips` 仅在本地显示出口 IP。第三方评分不是 Anthropic 的分数，也不是封号概率。

## 这套流程总结的经验

- 关闭本地 IPv6 不能决定远端节点的出口协议，必须测访问 Claude 的真实出口。
- DNS 劫持、fake-IP、加密 DNS 与 DNS 经过代理是不同检查项。
- DNS 检测变绿不代表国内/内网可访问，必须保留直连/分域 DNS，在用户实际浏览器测试常用网站。
- Claude 使用独立手动组；不反复切换日常总代理组，不盲目改道共享遥测和全局 NTP。
- 用订阅扩展/DNS 覆写持久化，检查运行内核，并重新激活确认保存。

[第三方域名指南](https://ip.net.coffee/claude/site.html) 提供了域名候选；实施前核对 [Mihomo DNS 官方文档](https://wiki.metacubex.one/config/dns/) 和 [Clash Verge 扩展行为](https://www.clashverge.dev/guide/extend.html)。项目不采用“NTP 揭示客户端时区”的说法，也不自动删除凭证或设备 ID。

## 隐私与验证

没有统计、自动上传、订阅导入或后台服务。在线测试按授权访问 trace 服务；风险查询和浏览器检测会联系第三方。备份、生成配置、检测报告不进入版本控制。提交 issue 时不要附真实订阅、凭据、完整配置、连接历史、私人 IP 或截图。GitHub 上的公开仓库归属自然可见。

```sh
python3 -m unittest discover -s tests -v
python3 tools/privacy_check.py
```

测试覆盖敏感字段排除、局部分流方案、中断后恢复代理组、非覆盖安装。隐私检查只是辅助，发布前仍需审查暂存文件。测试不连接真实节点、不调用付费 API。脱敏反馈要求见 [CONTRIBUTING.md](CONTRIBUTING.md)。

许可证：[MIT](LICENSE)。与 Anthropic、Clash Verge、MetaCubeX、Net.Coffee 无隶属关系。
