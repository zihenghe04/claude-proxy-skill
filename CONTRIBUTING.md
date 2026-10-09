# Contributing / 参与贡献

Use synthetic configurations and documentation-range IPs in tests. Describe the OS, client/core version, exact error category, expected route and actual route. Include only allowlisted summaries. Never attach full subscriptions, provider URLs, passwords, controller secrets, UUIDs, cookies, account/device identifiers, private paths, browsing logs or unredacted screenshots. Compare both Claude and ordinary direct/proxied websites when changing DNS behavior.

测试使用虚构配置和文档示例 IP。反馈包含系统、客户端/内核版本、错误类别、预期与实际分流，仅附白名单摘要。不要上传完整订阅、机场链接、密码、控制器密钥、UUID、Cookie、账号/设备标识、私人路径、浏览历史、未脱敏截图。修改 DNS 后须同时验证 Claude、日常直连和代理网站。

Run unit tests and the privacy check before opening a PR. Report a suspected exposure privately through a suitable channel rather than posting the secret in a public issue. Dependencies and domain coverage should be updated from current primary documentation.

提交 PR 前运行测试和隐私检查。发现可能的泄露时，不要将秘密发到公开 issue，使用合适的私有渠道。依赖和域名覆盖根据当前官方文档维护。
