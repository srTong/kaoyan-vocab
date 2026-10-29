# 考研英语词汇网站 - 部署指南

## 📋 目录
1. [Auth0 配置](#1-auth0-配置)
2. [网站配置](#2-网站配置)
3. [阿里云 OSS 部署](#3-阿里云-oss-部署)
4. [测试验证](#4-测试验证)

---

## 1. Auth0 配置

### 1.1 注册 Auth0 账号
1. 访问 [Auth0 官网](https://auth0.com/)
2. 点击 "Sign Up" 注册账号（支持 GitHub/Google 登录）
3. 选择 "Free" 免费计划（支持 7000 活跃用户）

### 1.2 创建应用
1. 登录后进入 Dashboard
2. 左侧菜单选择 "Applications" → "Applications"
3. 点击 "Create Application"
4. 填写信息：
   - **Name**: 考研英语词汇
   - **Application Type**: Single Page Web Application
   - 点击 "Create"

### 1.3 配置应用
在应用设置页面：

**Basic Information:**
- **Domain**: 复制你的域名（如 `dev-xxxxx.us.auth0.com`）
- **Client ID**: 复制你的客户端 ID

**Application URIs:**
- **Allowed Callback URLs**: 
  ```
  http://localhost:8080
  https://your-domain.com
  ```
- **Allowed Logout URLs**: 
  ```
  http://localhost:8080
  https://your-domain.com
  ```
- **Allowed Web Origins**: 
  ```
  http://localhost:8080
  https://your-domain.com
  ```

**Scroll down and click "Save Changes"**

### 1.4 配置认证方式
1. 左侧菜单 "Authentication" → "Database"
2. 点击 "Username-Password-Authentication"
3. 确保启用 "Requires Email Verification"（推荐）

### 1.5 记录配置信息
你需要以下信息：
- **Domain**: `dev-xxxxx.us.auth0.com`
- **Client ID**: `xxxxxxxxxxxxxxxxxxxx`

---

## 2. 网站配置

### 2.1 修改 Auth0 配置
编辑 `material/website/auth.js` 文件，替换以下配置：

```javascript
const AUTH0_CONFIG = {
    domain: 'YOUR_AUTH0_DOMAIN',        // 替换为你的 Auth0 域名
    clientId: 'YOUR_AUTH0_CLIENT_ID',   // 替换为你的 Auth0 客户端 ID
    audience: 'https://YOUR_AUTH0_DOMAIN/userinfo',
    redirectUri: window.location.origin + window.location.pathname,
    scope: 'openid profile email'
};
```

**示例：**
```javascript
const AUTH0_CONFIG = {
    domain: 'dev-abc123.us.auth0.com',
    clientId: 'Abc123Def456Ghi789Jkl012Mno345',
    audience: 'https://dev-abc123.us.auth0.com/userinfo',
    redirectUri: window.location.origin + window.location.pathname,
    scope: 'openid profile email'
};
```

### 2.2 本地测试
在本地测试登录功能：

```bash
cd material/website
python3 -m http.server 8080
```

访问 `http://localhost:8080`，测试：
- ✅ 登录按钮显示
- ✅ 点击登录跳转到 Auth0
- ✅ 注册/登录后跳转回网站
- ✅ 显示用户头像和名称
- ✅ 登出功能正常

---

## 3. 阿里云 OSS 部署

### 3.1 开通 OSS 服务
1. 访问 [阿里云官网](https://www.aliyun.com/)
2. 登录/注册账号
3. 产品菜单 → "对象存储 OSS"
4. 点击 "立即开通"（按量付费，费用极低）

### 3.2 创建 Bucket
1. 进入 OSS 控制台
2. 点击 "创建 Bucket"
3. 填写信息：
   - **Bucket 名称**: `kaoyan-vocab`（或其他名称）
   - **地域**: 选择离你最近的地区（如华东1-杭州）
   - **存储类型**: 标准存储
   - **读写权限**: 公共读
   - **其他**: 保持默认
4. 点击 "确定"

### 3.3 配置静态网站托管
1. 进入刚创建的 Bucket
2. 左侧菜单 "基础设置" → "静态页面"
3. 点击 "设置"：
   - **启用静态页面托管**: ✅ 勾选
   - **默认首页**: `index.html`
   - **默认404页**: `index.html`（单页应用需要）
4. 点击 "保存"

### 3.4 上传网站文件
**方法一：控制台上传**
1. 在 Bucket 页面，点击 "文件管理"
2. 点击 "上传文件"
3. 将 `material/website/` 目录下的所有文件拖拽上传
4. 等待上传完成

**方法二：ossutil 工具（推荐）**
```bash
# 安装 ossutil
# macOS
brew install aliyun-cli

# 配置凭证
aliyun configure

# 上传文件
aliyun oss cp -r material/website/ oss://kaoyan-vocab/ --meta Cache-Control:no-cache
```

### 3.5 获取访问地址
上传完成后，在 "静态页面" 设置中可以看到访问地址：
```
http://kaoyan-vocab.oss-cn-hangzhou.aliyuncs.com
```

### 3.6 更新 Auth0 回调地址
1. 回到 Auth0 Dashboard
2. 进入你的应用设置
3. 在 "Allowed Callback URLs" 添加：
   ```
   http://kaoyan-vocab.oss-cn-hangzhou.aliyuncs.com
   ```
4. 在 "Allowed Logout URLs" 添加：
   ```
   http://kaoyan-vocab.oss-cn-hangzhou.aliyuncs.com
   ```
5. 在 "Allowed Web Origins" 添加：
   ```
   http://kaoyan-vocab.oss-cn-hangzhou.aliyuncs.com
   ```
6. 点击 "Save Changes"

---

## 4. 测试验证

### 4.1 功能测试清单
- [ ] 访问网站地址，页面正常加载
- [ ] 右上角显示"登录"按钮
- [ ] 点击登录，跳转到 Auth0 登录页
- [ ] 注册新账号并登录
- [ ] 登录成功后跳转回网站
- [ ] 显示用户头像和名称
- [ ] 点击"开始练习"进入练习页面
- [ ] 完成一组练习
- [ ] 查看浏览器控制台，确认学习进度已保存
- [ ] 点击"登出"，成功退出

### 4.2 性能测试
- [ ] 页面加载速度 < 3秒
- [ ] 登录跳转流畅
- [ ] 练习页面交互响应迅速

### 4.3 移动端测试
- [ ] 手机访问网站正常显示
- [ ] 登录功能正常
- [ ] 练习功能正常

---

## 💰 成本估算

### Auth0（免费计划）
- 活跃用户：7,000 个免费
- 登录次数：不限
- 社交登录：支持（Google、GitHub、微信等）
- **费用：¥0/月**

### 阿里云 OSS
- 存储费用：¥0.12/GB/月（100MB ≈ ¥0.012/月）
- 流量费用：¥0.25/GB（下行流量）
- 请求费用：¥0.01/万次
- **预估费用：¥1-5/月**（取决于访问量）

### 总成本
**约 ¥1-5/月**（超低成本！）

---

## 🔧 高级配置（可选）

### 自定义域名
如果你想使用自己的域名（如 `vocab.yourdomain.com`）：

1. **OSS 绑定自定义域名**
   - Bucket → "域名管理" → "绑定用户域名"
   - 输入你的域名，按提示添加 CNAME 解析

2. **Auth0 更新回调地址**
   - 添加你的自定义域名到回调 URL 列表

3. **申请 SSL 证书**（HTTPS）
   - 阿里云提供免费 SSL 证书
   - 在 "域名管理" → "证书托管" 中配置

### CDN 加速
如果用户遍布全国，可以开启 CDN：
1. 阿里云控制台 → "CDN"
2. 添加加速域名（你的 OSS 域名或自定义域名）
3. 配置回源到 OSS
4. **费用：约 ¥0.1/GB 流量**

---

## 📞 常见问题

### Q: 登录后跳转回网站报错？
A: 检查 Auth0 的 "Allowed Callback URLs" 是否包含你的网站地址。

### Q: 用户头像不显示？
A: 可能是跨域问题，检查 Auth0 配置中的 "Allowed Web Origins"。

### Q: 学习进度没有保存？
A: 打开浏览器控制台查看错误信息，确认 `auth.js` 和 `practice.js` 正确加载。

### Q: OSS 上传后页面 404？
A: 检查是否启用了"静态页面托管"，并设置默认首页为 `index.html`。

---

## 📚 参考资源

- [Auth0 文档](https://auth0.com/docs)
- [阿里云 OSS 文档](https://help.aliyun.com/product/31815.html)
- [Auth0 SPA JS SDK](https://github.com/auth0/auth0-spa-js)

---

## ✅ 部署完成检查清单

- [ ] Auth0 应用已创建并配置
- [ ] `auth.js` 中的配置已更新
- [ ] 本地测试通过
- [ ] OSS Bucket 已创建
- [ ] 静态网站托管已启用
- [ ] 网站文件已上传
- [ ] Auth0 回调地址已更新
- [ ] 在线测试通过

**恭喜！你的考研词汇网站已成功部署！** 🎉
