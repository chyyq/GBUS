# GBUS 美股四仓量化网站

这是一个可直接发布到 GitHub Pages 的静态量化看板。页面主体在 `docs/`，每日数据生成脚本在 `scripts/generate-data.py`，GitHub Actions 工作流在 `.github/workflows/deploy-pages.yml`。

## 功能

- 每日拉取 Yahoo Finance 的真实日线 OHLCV 与新闻，拉取 Nasdaq screener 的市值和上市交易所字段。
- 按上传文档中的 A/B/C/D 四仓逻辑输出推荐股票、买点、卖点目标与预测时间窗、止损价。
- 页面使用 `localStorage` 保存用户输入的持仓、买入价、股数和备注。
- 若用户没有输入买入价，推荐标的只作为观察项，不触发卖点或止损提醒。
- 持仓输入后，页面会按最新数据提示止损、第一卖点、第二卖点和短线时间止损。
- 可选配置 `X_BEARER_TOKEN` 后，每日拉取并总结 Serenity 的 X 最新讯息。

## 本地运行

```bash
python scripts/generate-data.py
npm run serve
```

打开 `http://localhost:4173`。

## GitHub Pages 发布

1. 把本仓库推送到 GitHub。
2. 推荐在仓库 `Settings -> Pages` 中把 Source 设为 `GitHub Actions`。
3. 进入 `Actions -> Daily Quant Site`，点击 `Run workflow` 验证一次。
4. 推送代码时会自动发布；之后工作流还会按 `35 22 * * 1-5` UTC 自动运行，即美股交易日收盘后更新页面。

仓库地址和网站地址不是同一个页面。仓库通常是
`https://github.com/用户名/仓库名`，网站地址通常是
`https://用户名.github.io/仓库名/`。

为了兼容已有 Pages 设置，仓库根目录和 `docs/` 都包含网站入口：

- 选择 `GitHub Actions`：发布 `_site` 构建产物。
- 选择 `Deploy from a branch -> main -> /(root)`：直接使用根 `index.html`。
- 选择 `Deploy from a branch -> main -> /docs`：直接使用 `docs/index.html`。

三种方式都会打开量化看板，不会再由 README 充当首页。

## Serenity / X 配置

X 登录内容无法稳定匿名抓取。若需要自动读取 `https://x.com/aleabitoreddit` 的最新内容，请在 GitHub 仓库中添加 Secret：

- `Settings -> Secrets and variables -> Actions -> New repository secret`
- Name: `X_BEARER_TOKEN`
- Value: 你的 X API v2 Bearer Token

未配置时，页面会显示“等待配置”，不会伪造或缓存不可靠推文。

## 数据边界

默认无密钥数据源为 Yahoo Finance Chart、Yahoo Finance Search 和 Nasdaq screener。脚本会记录本次运行警告；如果个别股票的财务增速、财报日期或新闻缺失，页面会标出风险标签。该网站是交易辅助工具，不构成投资建议。
