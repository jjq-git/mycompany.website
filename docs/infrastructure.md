# 基础设施：CDN、域名、SSL 自动化

> 本文档讲**输出去哪、怎么去**。生成什么静态文件见 [output.md](site/output.md)。

## 一、为什么要 API 自动化

如果靠人工：每加一个用户就要建桶、配 CDN、签 SSL、绑域名 —— 10 分钟一个，
100 个用户就是 16 小时人工。规模化必死。

所以：建桶、上传、绑域名、签 SSL，**全部 API 调用 + 状态机管理**。

## 二、云厂商选型决策

### 决策结论

**MVP 阶段：阿里云 OSS + CDN + 云解析（性能）+ Let's Encrypt（SSL）**。

理由：

- 目标用户 4 类（制造业 / 餐饮 / 服务业 / 贸易）中 3 类需要国内访问最快 → 阿里云 CDN
- 阿里云 ICP 备案配套
- 一个账号一套 API（OSS / CDN / DNS），运维简单
- SSL 用 Let's Encrypt（**无配额限制**），通过 ACME 流程申请，证书部署到阿里云 CDN（详见五）

### 其他选项与判断

| 方案 | 国内速度 | SSL 方案 | 适合 |
|---|---|---|---|
| **阿里云 OSS+CDN + Let's Encrypt** | 最快 | ACME 自动签 + 续期 | ✅ MVP |
| 阿里云 + 阿里云免费证书 | 最快 | 配额 20 张/年/账号 + 3 个月期 | 不推荐（早晚要换） |
| Cloudflare for SaaS | CDN 国内访问不稳（500ms-5s） | 完全自动 | 海外为主 |
| AWS S3 + CloudFront | 国内慢 | 自动 | 不推荐 |
| 腾讯云 EdgeOne | 快 | 类似阿里云 | 备选 |
| 自建 Caddy | 看服务器位置 | Caddy 自动 | 增加运维负担 |

### 为什么不用 Cloudflare（虽然 SSL 全自动）

Cloudflare 在国内访问不稳定（500ms - 5s，时段差异大，电信尤其差）。

国内典型对比：

```text
                  上海移动  北京电信  广州联通
Cloudflare R2     800ms     2.5s     1.2s
阿里云 CDN杭州    50ms      80ms     60ms
```

20-50 倍差距。给做国内生意的小企业用 = 砸口碑。

### 远期：可选 Cloudflare

数据库 `sites.cdn_provider` 字段已留好：

- 默认 `aliyun`（国内客户）
- 可选 `cloudflare`（出口贸易客户）

不要 MVP 就做多 CDN 抽象层 —— 复杂度提前透支。
真有跨地域需求时再加。

## 三、桶模式：共享 vs 独立

### MVP 推荐：共享桶 + 路径分割

| | 共享桶（推荐） | 每用户独立桶 |
|---|---|---|
| 创建成本 | 0 | 每个站调一次 API |
| 运维复杂度 | 低 | 中（管 1000+ 桶） |
| 隔离性 | 弱（路径权限） | 强 |
| 桶数限额 | 不受限 | 阿里云默认 100，可申请 |
| 给用户"完全所有权" | 难（要导出） | 易（直接转交 access key） |

### 演进路径

```text
MVP:        共享桶 + 路径前缀（site.bucket_path_prefix = "youngku/"）
              ↓
Phase 2:    可选独立桶（完全自主可控）
              ↓
Phase 3:    BYOC（Bring Your Own Cloud）—— 客户用自己的云账号
```

DB `sites.storage_mode` 字段已留好（`shared` / `dedicated`）。

## 四、自定义域名的完整链路

整个流程涉及 4 个云资源 + 客户的 1 个动作（配 DNS）。

### 阿里云路径

```text
用户在后台输入 "company-a.com"
        ↓
1. 后台调 AddCdnDomain
   → CDN 新增加速域名（status: pending verification）
   → 云返回一个 CNAME 目标（如 yyy.cdn.aliyuncs.com）
        ↓
2. 后台显示 CNAME 配置指引给用户
   → "请把 company-a.com CNAME 解析到 yyy.cdn.aliyuncs.com"
        ↓
3. 用户去他的域名服务商配 CNAME
   → 这一步需要等
        ↓
4. 后台轮询 DescribeDomainCertificateInfo（每分钟一次）
   → 检查 DNS 是否生效
   → DNS 生效 → 推进到下一步
        ↓
5. 后台启动 ACME 流程申请 Let's Encrypt 证书（详见五）
   → DNS-01 验证（通过 CNAME 委托写 TXT 到我们的子域）
   → 拿到 cert.pem + privkey.pem
        ↓
6. 后台调 SetCdnDomainSSLCertificate
   → 把 PEM 证书 + 私钥上传到阿里云 CDN
   → CDN 节点 1-2 分钟内全网生效
        ↓
7. 后台调 EnableCdnDomain
   → 启用加速
        ↓
8. 通知用户：✅ 已上线
```

### 这个流程的代码结构

每一步都是一个 `provisioning_jobs` 记录。状态机驱动：

```text
job_type            状态机
─────────────────────────────────────────
add_cdn_domain    → pending → success → 触发轮询任务
check_dns         → 定时跑，DNS 生效 → 触发下一步
issue_ssl         → 申请证书
deploy_ssl        → 部署到 CDN
enable_cdn        → 启用
```

任何一步失败：

- 标记 `status = failed`
- 记 `last_error`
- 满足条件可重试（`attempts < 3`）
- 超过重试上限发邮件告警

## 五、SSL：Let's Encrypt + ACME + 阿里云 CDN

整套包括：申请 + 部署 + 续期。
不用阿里云免费证书（3 个月期 + 20 张/年配额，规模化早晚要换），一步到位用 Let's Encrypt。

### 5.1 为什么用 Let's Encrypt 而不是阿里云免费证书

| 维度 | 阿里云免费 | Let's Encrypt |
|---|---|---|
| 期限 | 3 个月 | 3 个月（一样） |
| 配额 | 20 张/年/账号 | 50 张/周/注册域 |
| 配额超了怎么办 | 必须迁方案 | 不会超 |
| 集成成本 | 低（阿里云 SDK） | 中（ACME 库） |
| 续期复杂度 | 一样 | 一样 |

MVP 直接用 LE 比"先阿里云、规模化再迁"省事 —— 多写一周代码省掉日后整体重构。

### 5.2 关键认识：阿里云 CDN 接受任意 PEM 证书

证书可以不来自阿里云。给 CDN 一份 PEM + 私钥，它就能用：

```text
Let's Encrypt 签证书 (cert.pem + privkey.pem)
        ↓
调阿里云 CDN SetCdnDomainSSLCertificate API
        ↓
CDN 节点几秒内开始用新证书提供 HTTPS
```

### 5.3 ACME 申请流程（每张证书）

```text
1. 启动 ACME order 向 Let's Encrypt:
   "我要 company-a.com 的证书"
        ↓
2. Let's Encrypt 返回挑战:
   "在 _acme-challenge.company-a.com 写 TXT: <token>"
        ↓
3. 后台调 DNS API 写 TXT 记录（详见 5.4 CNAME 委托）
        ↓
4. 等 30 秒 DNS 传播
        ↓
5. 通知 Let's Encrypt 验证
        ↓
6. Let's Encrypt 验证成功 → 签证书
        ↓
7. 后台拿到 cert.pem + privkey.pem
        ↓
8. 调阿里云 CDN API 部署（详见 5.5）
```

推荐 Python 库：**certbot 的 `acme` 包**（官方维护、稳定）。
包装成 200-400 行的 `LetsEncryptIssuer` 类。

### 5.4 CNAME 委托：解决客户 DNS 不在阿里云的问题

客户域名的 DNS 可能在 GoDaddy / Cloudflare DNS / 华为云 DNS，**不一定在阿里云**。
强制要求客户迁 DNS 不现实。

解法：让客户配一个**一次性 CNAME 委托**：

```text
客户的 DNS 设置:
    company-a.com                  CNAME  yyy.cdn.aliyuncs.com
    _acme-challenge.company-a.com  CNAME  acme.mycompany.website
```

第二条把 ACME 验证"委托"给我们的子域。
我们只需在 acme.mycompany.website 的 DNS 里写 TXT 记录（这是我们自己的 DNS，可控）。
Let's Encrypt 跟着 CNAME 走，验证成功。

好处：

- 客户配置一次，永久有效
- 续期、签新证书都不再麻烦客户
- 客户的 DNS 提供商是谁都行

### 5.5 部署到阿里云 CDN

```text
调用: SetCdnDomainSSLCertificate
参数:
    DomainName    = "company-a.com"
    SSLPub        = <cert.pem 内容>
    SSLPri        = <privkey.pem 内容>
    CertType      = "upload"      （上传型，非阿里云签）
    SSLProtocol   = "on"
```

返回成功 → CDN 节点 1-2 分钟内全网生效。

### 5.6 自动续期

90 天周期，提前 30 天开始续。

```text
后台 cron job（每天 00:00 跑）:
    SELECT * FROM domains
    WHERE ssl_expires_at < NOW() + INTERVAL '30 days'
      AND status = 'active'
        ↓
    对每条:
        创建 provisioning_job(job_type='renew_letsencrypt')
        异步执行:
            重走 ACME 流程（5.3）
            部署到 CDN（5.5）
            更新 domains.ssl_expires_at
        ↓
    失败任务每天再试一次
    距过期 < 7 天还没续上 → 紧急告警 + 站长邮件
    过期 → 强制用户重新走"绑域名"流程
```

每张证书每年续 4-5 次，对小企业 SaaS 完全可控。

### 5.7 Let's Encrypt 速率限制

| 限制 | 数值 | 实际影响 |
|---|---|---|
| 同一注册域名 | 50 张/周 | 50 个新客户/周以内不触发 |
| 失败验证 | 5 次/小时 | 出错时要退避 |
| 同一 SAN 重复 | 5 张/周 | 续期不触发 |
| 通配符证书 | 必须 DNS-01 | 我们方案就是 DNS-01 |

50 张/周 = 200 张/月 = 2400 张/年，对小企业 SaaS 远够用。

真爆量了：

- 申请 Let's Encrypt 速率提升（免费）
- 或换 ZeroSSL（同样支持 ACME，限额更宽松）

### 5.8 私钥存储

证书私钥极敏感。绝不能：

- ❌ 存数据库明文
- ❌ 提到 git
- ❌ 写日志

应该：

- ✅ 存阿里云 KMS / OSS 加密 bucket
- ✅ 或者本地 secrets/ 文件夹（gitignored，权限 600）
- ✅ 上传到 CDN 后本地副本可删（下次续期重新签即可）

## 六、反模式：用 SAN 证书省事（千万别这样）

阿里云客服 / AI 偶尔会推荐"一张 SAN 证书覆盖多个域名以简化管理"。
**对自家有多域名的单一企业可以，对我们这种 SaaS 多租户是反模式**。

### 看似省事，实际 4 个真问题

| 问题 | 说明 |
|---|---|
| **隐私泄漏** | 任何人 `openssl s_client` 一查证书的 SAN 字段，能看到其它客户的域名。竞争对手互相暴露。 |
| **牵一发动全身** | 加新客户 / 老客户取消 → 重签证书 → 所有域名同时短暂中断 |
| **故障爆炸半径** | 一张证书出问题 → 一批客户一起挂 |
| **限额最终卡住** | SAN 证书上限 100-250 个域名，规模化后管理多张 SAN 证书 = 噩梦 |

### 我们的做法

**每个客户域名一张独立证书**，互不影响：

```text
对每个客户域名:
    一张独立的阿里云免费 DV 证书
    一个独立的 CDN 加速域名
    一份独立的续期记录
```

代价：

- 数据库 `domains` 行多一些（无所谓）
- 续期任务跑得多一些（每域名 1 次/年，CPU 几乎为零）

收益：

- 隐私隔离
- 故障隔离
- 客户来去互不影响
- 没有 SAN 上限

### 提示

未来 AI / 客服再推荐 SAN 方案，先反问："这是给单租户的还是多租户的？"
对 SaaS 平台，**单租户思路全部要反向校验**。

## 七、provisioning_jobs 表的作用

这张表是**所有云资源自动化的事务总账**（数据库后期表，索引见 [database.md](database.md)）。

为什么需要：

1. **云 API 不立刻成功** —— DNS 生效要等几分钟到几小时
2. **要重试** —— 网络抖动 / 云那边偶尔抽风
3. **要审计** —— 出问题能查为什么、什么时候
4. **要可恢复** —— 平台重启不能丢任务

一个 worker 进程持续扫这张表，按状态机推进任务。

## 八、凭证管理

云 API key 是高敏感信息。**绝不写代码、不进 git**。

### 开发环境

```text
.env.local（gitignored）:
    ALIYUN_ACCESS_KEY_ID=xxx
    ALIYUN_ACCESS_KEY_SECRET=xxx
    ALIYUN_OSS_BUCKET=mycompany-dev
```

### 生产环境

| 方案 | 适用 |
|---|---|
| 环境变量 + systemd EnvironmentFile | 单机 MVP |
| Docker secrets | 容器化部署 |
| 阿里云 KMS + RAM 角色 | 阿里云 ECS 部署，最安全 |

### 最小权限

不要给后台账号 root 权限。专门建一个 RAM 用户，只给：

- OSS 的特定 bucket 读写
- CDN 域名的增删改
- SSL 证书的申请 / 部署
- DNS 的特定区域读写

## 九、错误处理 / 重试策略

### 应该重试的错误

```text
- 网络超时 / 连接失败
- 5xx 服务器错误
- 限流（429）→ 加退避
- 资源还在创建中（202）
```

### 不应该重试的错误

```text
- 4xx 客户端错误（参数错）
- 权限不足（403）
- 资源不存在（404）
- 余额不足
```

### 退避策略

```text
attempt 1: 立即
attempt 2: 等 30 秒
attempt 3: 等 5 分钟
attempt 4+: 标记失败，告警
```

## 十、清理任务

用户取消订阅 / 删除站点后：

```text
T+0:    soft_deleted_at 记录
        网站继续在 CDN 上（30 天宽限期）
        ↓
T+30:   触发 cleanup provisioning_jobs:
            - 删除 OSS 中的所有文件
            - 解绑 CDN 域名
            - 撤销 SSL 证书
            - 删除 sites/<id>/ 文件夹
            - 数据库 sites 行硬删除（保留 owner 邮件、发布历史不删）
```

清理任务也走 `provisioning_jobs`，便于追踪和重试。

## 十一、监控指标

后台仪表盘至少展示：

| 指标 | 阈值告警 |
|---|---|
| pending 状态的 provisioning_jobs 数 | > 50 |
| failed 状态的 provisioning_jobs 数（24h）| > 10 |
| 30 天内即将过期的 SSL 数 | > 0（提示续期任务在跑） |
| OSS 总存储量 | 接近账号配额 |
| CDN 当月流量 | 接近预算 |
| 域名验证 pending > 7 天的 | > 0（用户可能忘了配 DNS） |

## 十二、给开发的实操建议

1. **先写 mock provider**：本地开发不要真调阿里云 API，写一个 `MockCDNProvider` 返回假数据
2. **每个 API 调用记审计日志**：阿里云控制台不全展示历史，自己存
3. **状态机用枚举类**：避免字符串比较出错
4. **provisioning_jobs 是幂等的**：重试不能创建重复资源（用 `external_id` 检查已存在）
5. **客户配 DNS 这一步要明确反馈**：后台显示"等待 DNS 生效... 上次检查 3 分钟前"
6. **慢任务进度可见**：自定义域名要等几分钟到几小时，要让客户知道在跑

## 十三、阶段路线图

| 阶段 | 完成什么 |
|---|---|
| **M5（MVP 发布）** | 共享桶 + 平台子域名（slug.mycompany.website） + 平台域名的 SSL（一次性配） |
| **M6（自定义域名）** | 域名 API + 阿里云免费 SSL 自动签 + 续期任务 |
| **Phase 2** | 可选独立桶 |
| **Phase 3** | 多 CDN 支持（加 Cloudflare 给海外客户） |

每阶段对应的 `provisioning_jobs` job_type 增量加。
