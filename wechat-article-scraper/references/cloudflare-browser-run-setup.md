# Cloudflare Browser Run API 配置指南

> 原名 **Browser Rendering**，2026年更名为 **Browser Run**。API端点仍保留 `/browser-rendering/` 路径。

## 前置条件

- Cloudflare 账户（无需域名）
- Workers Free 计划即可（每日赠送10分钟浏览器时间）

## 配置步骤

### Step 1: 开通 Browser Run 服务

1. 登录 https://dash.cloudflare.com
2. 左侧菜单 → **Workers 和 Pages**
3. 找到 **浏览器渲染**（Browser Rendering）/ **Browser Run**
4. 点击 **激活**

### Step 2: 创建 API 令牌

在 Cloudflare 控制台创建自定义 API 令牌，**关键权限**：

| 设置项 | 值 |
|--------|-----|
| 令牌名称 | `hermes-browser-run` |
| 权限 - 账户 | **浏览器渲染 → 编辑**（⚠️ 必选，仅选 Workers 不够） |
| 账户资源 | 包括所有账户 |

创建流程：
1. 右上角头像 → 我的个人资料 → API令牌 → 创建令牌
2. 选择「自定义令牌」
3. 配置权限后点击「继续以显示摘要」
4. 点击「创建令牌」，**立即复制令牌**（只显示一次）

### Step 3: 配置环境变量

```bash
echo 'export CLOUDFLARE_ACCOUNT_ID="你的32位账户ID"' >> ~/.bashrc
echo 'export CLOUDFLARE_API_TOKEN="你的API令牌"' >> ~/.bashrc
source ~/.bashrc
```

## 验证连通性

```bash
# 验证账户API
curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"

# 验证Browser Run（截取示例页面截图）
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/browser-rendering/screenshot" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}' \
  --output /tmp/test.png
```

## 故障排查

### 常见错误

| 错误码 | 信息 | 原因 | 解决 |
|--------|------|------|------|
| `10000` | Authentication error | Token 无效或缺少权限 | 检查 Token 是否已过期，是否包含「浏览器渲染 - 编辑」权限 |
| `7003` | Could not route to /accounts/... | URL 中账户 ID 错误或 Token 无此权限 | 确认账户 ID 正确 |
| `1000` | Invalid API Token | Token 格式错误 | 重新创建 Token |

### Token 权限验证

```bash
# 测试账户级 API
curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('✅' if d.get('success') else '❌', d.get('errors',''))"

# 测试 Browser Rendering API
curl -s -o /dev/null -w "%{http_code}" -X POST \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/browser-rendering/screenshot" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
# 应返回 200
```

## 注意事项

- **账户 ID** 在 Cloudflare 控制台 URL 中可见：`https://dash.cloudflare.com/{account_id}`
- Token 创建后**只显示一次**，务必立即复制保存
- Workers Free 计划已包含 Browser Run，无需付费即可测试
- API 令牌不可泄露，泄露后立即到 Cloudflare 后台删除并重新生成
