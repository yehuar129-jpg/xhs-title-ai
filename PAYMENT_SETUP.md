# 个人收款 MVP 配置

当前项目已调整为“个人收款码 + 人工确认开通 Pro”的 MVP 模式。

用户流程：

1. 用户点击升级 Pro。
2. 选择支付宝或微信支付。
3. 页面显示你的个人收款码、金额和订单号。
4. 用户扫码付款，并提交付款备注。
5. 你确认到账后，在管理员订单页点击“确认开通”。
6. 用户刷新首页后变成 Pro。

## Render 环境变量

在 Render 后台进入你的服务：

`Environment` -> `Add Environment Variable`

填写：

```text
PAYMENT_PROVIDER=personal
PRO_PRICE=0.01
ADMIN_SECRET=QQ695976287..
ALIPAY_QR_URL=d:\xwechat_files\wxid_ogllovh8cbfd22_3a3e\temp\RWTemp\2026-06\35a4c13b6f4ae804593f5221b4225039.jpgURL
WXPAY_QR_URL=d:\xwechat_files\wxid_ogllovh8cbfd22_3a3e\temp\RWTemp\2026-06\b8f22ad687626cdd1be4c8788fe98c08.jpgURL
```

如果你暂时只有一个收款码，也可以只填：

```text
PERSONAL_PAY_QR_URL=你的收款码图片URL
```

系统会把它同时用于支付宝和微信入口。

## 管理员订单页

部署后打开：

```text
https://你的Render域名/admin_orders?admin_key=你的管理员密钥
```

看到用户提交的订单后，先在支付宝/微信里确认到账，再点击“确认开通”。

## 测试建议

先把价格设成：

```text
PRO_PRICE=0.01
```

自己扫码支付一笔，确认：

1. 付款页能展示收款码。
2. 用户提交付款确认后，订单变成 `reviewing`。
3. 管理员订单页能看到订单。
4. 点击“确认开通”后，用户变成 Pro。

跑通后再改成正式价格，例如 `19.90`、`29.90` 或 `49.00`。
