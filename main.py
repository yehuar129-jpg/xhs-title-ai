from datetime import date, datetime
import hashlib
import hmac
import os
from pathlib import Path
from typing import Dict, List, Literal, Optional
from urllib.parse import parse_qs, urlencode
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field


app = FastAPI(title="小红书爆款标题AI Pro")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FREE_DAILY_LIMIT = 5
FREE_TITLE_COUNT = 5
PRO_TITLE_COUNT = 50
PRO_PRICE = os.getenv("PRO_PRICE", "19.90")

users: Dict[str, Dict[str, object]] = {}
orders: Dict[str, Dict[str, object]] = {}


class GenerateRequest(BaseModel):
    keyword: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)


class TitleItem(BaseModel):
    title: str
    type: str
    score: int
    reason: str


class GenerateResponse(BaseModel):
    plan: Literal["free", "pro"]
    usage_left: int
    titles: List[TitleItem]


class CreateOrderRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    pay_type: Literal["alipay", "wxpay"] = "alipay"


class PaymentProofRequest(BaseModel):
    order_id: str = Field(..., min_length=1)
    contact: str = ""
    note: str = ""


TITLE_STRATEGIES = {
    "情绪冲击型": {
        "short": ["现在才懂，{keyword}最狠的不是努力，是这一步"],
        "pro": [
            "后悔没早点知道，{keyword}真正拉开差距的是这3个细节",
            "我做{keyword}踩过的坑，终于被这套方法治好了",
            "{audience}别硬扛了，{keyword}这样做真的轻松很多",
            "被{keyword}折磨过的人，看到第2点会沉默",
            "原来{keyword}不是我不行，是一直用错了方法",
            "把{keyword}做好以后，我才知道稳定变好有多爽",
            "如果你也被{keyword}卡住，这篇真的建议收藏",
            "{keyword}这件事，一旦开窍就很难回到从前",
            "我愿称之为{keyword}新手最值得补的一课",
            "{keyword}别再靠感觉了，这套思路更适合普通人",
        ],
        "reason": "用强情绪和真实感制造停留，适合拉高点击欲望。",
    },
    "强反差型": {
        "short": ["别人做{keyword}靠硬卷，我靠这个反而更稳"],
        "pro": [
            "同样做{keyword}，为什么别人轻松出效果？差别在这里",
            "{keyword}不是越贵越好，普通人更该先看这套判断法",
            "我以为{keyword}要拼资源，后来发现拼的是顺序",
            "90%的人把{keyword}做复杂了，其实先抓这1点",
            "{keyword}看起来很难，拆开后反而只有这几步",
            "别再盲目学{keyword}，真正有效的是反着做这件事",
            "花很多时间做{keyword}没效果？可能方向一开始就反了",
            "高手做{keyword}不靠灵感，靠的是这套固定结构",
            "新手做{keyword}最容易输在努力太平均",
            "越想把{keyword}做好，越要先放弃这3个动作",
        ],
        "reason": "用认知反差打破预期，让标题更容易被点开。",
    },
    "种草转化型": {
        "short": ["{keyword}新手直接抄这套，省心又容易出效果"],
        "pro": [
            "{keyword}想少走弯路，先把这套清单用起来",
            "实测有效的{keyword}方法，适合{audience}直接照做",
            "{keyword}闭眼入门方案：低成本、好执行、反馈快",
            "最近最满意的{keyword}思路，真的比乱试强太多",
            "{keyword}不想再瞎试，这套组合可以先安排上",
            "把{keyword}做顺以后，我最想推荐的是这5个动作",
            "{keyword}从0到1，这套模板比搜一堆攻略更省时间",
            "预算有限也能做好{keyword}，关键是先选对路径",
            "想提升{keyword}效率，这个方法值得直接收藏",
            "{keyword}入门别贪多，先用这一套就够了",
        ],
        "reason": "突出可复制、低门槛和收益感，更适合引导收藏与转化。",
    },
    "痛点解决型": {
        "short": ["{keyword}一直没起色？问题大多出在这3点"],
        "pro": [
            "{keyword}做不好不是没天赋，先排查这5个痛点",
            "{keyword}总是卡住？把这几个问题改掉就顺很多",
            "{audience}做{keyword}最常见的误区，我一次讲清楚",
            "{keyword}没效果别急，先看你是不是漏了这一步",
            "真正拖慢{keyword}的，不是能力，是这几个坏习惯",
            "{keyword}越做越累？这套优化顺序能帮你减负",
            "做{keyword}反复失败的人，通常都忽略了这个前提",
            "{keyword}低效的根源，可能藏在你每天重复的动作里",
            "如果{keyword}迟迟没有反馈，先从这4处开始改",
            "{keyword}避坑指南：这些错误越早改越省钱",
        ],
        "reason": "直接命中焦虑和阻碍，给用户明确的解决期待。",
    },
    "好奇悬念型": {
        "short": ["我把{keyword}坚持7天，结果和想象完全不一样"],
        "pro": [
            "我用一个小调整测试{keyword}，结果第3天就变了",
            "{keyword}真正有效的关键，我试完才敢说",
            "为什么你做{keyword}没反馈？答案藏在这个细节里",
            "坚持{keyword}一周后，我发现最重要的不是技巧",
            "{keyword}到底有没有用？我把过程和结果都整理好了",
            "一个被忽略的{keyword}方法，试过才知道有多香",
            "我拆了20个{keyword}案例，发现爆起来都有同一个点",
            "{keyword}看似玄学，其实有一条很清晰的逻辑",
            "做{keyword}前先问自己这个问题，结果会差很多",
            "我以为{keyword}靠运气，直到看到这组规律",
        ],
        "reason": "保留信息缺口，激发继续阅读和收藏的动机。",
    },
}

AUDIENCES = ["新手", "普通人", "小团队", "副业人群", "内容创作者"]


def today_key() -> str:
    return date.today().isoformat()


def ensure_user(user_id: str) -> Dict[str, object]:
    user = users.setdefault(
        user_id,
        {"user_id": user_id, "plan": "free", "used_today": 0, "usage_date": today_key()},
    )
    if user["usage_date"] != today_key():
        user["used_today"] = 0
        user["usage_date"] = today_key()
    return user


def usage_left(user: Dict[str, object]) -> int:
    if user["plan"] == "pro":
        return -1
    return max(0, FREE_DAILY_LIMIT - int(user["used_today"]))


def score_for(title_type: str, index: int, is_pro: bool) -> int:
    base = 88 if is_pro else 80
    type_bonus = list(TITLE_STRATEGIES).index(title_type)
    return min(99, base + ((index * 3 + type_bonus * 2) % 12))


def build_titles(keyword: str, is_pro: bool) -> List[TitleItem]:
    keyword = keyword.strip()
    titles: List[TitleItem] = []
    variants = 10 if is_pro else 1
    template_key = "pro" if is_pro else "short"

    for index in range(variants):
        for title_type, strategy in TITLE_STRATEGIES.items():
            templates = strategy[template_key]
            title = templates[index % len(templates)].format(
                keyword=keyword, audience=AUDIENCES[index % len(AUDIENCES)]
            )
            titles.append(
                TitleItem(
                    title=title[:48],
                    type=title_type,
                    score=score_for(title_type, index, is_pro),
                    reason=strategy["reason"],
                )
            )
    return titles[: PRO_TITLE_COUNT if is_pro else FREE_TITLE_COUNT]


def mark_user_pro(user_id: str, order_id: Optional[str] = None) -> Dict[str, object]:
    user = ensure_user(user_id)
    user["plan"] = "pro"
    if order_id and order_id in orders:
        orders[order_id]["status"] = "paid"
        orders[order_id]["paid_at"] = datetime.utcnow().isoformat()
    return user


def build_epay_sign(params: Dict[str, str], merchant_key: str) -> str:
    sign_items = [
        f"{key}={params[key]}"
        for key in sorted(params)
        if key not in {"sign", "sign_type"} and params[key] != ""
    ]
    sign_text = "&".join(sign_items) + merchant_key
    return hashlib.md5(sign_text.encode("utf-8")).hexdigest()


def build_generic_sign(params: Dict[str, str], secret: str) -> str:
    sign_text = "&".join(f"{key}={params[key]}" for key in sorted(params) if key != "sign")
    return hmac.new(secret.encode("utf-8"), sign_text.encode("utf-8"), hashlib.sha256).hexdigest()


def build_pay_url(request: Request, user_id: str, order_id: str, pay_type: str) -> str:
    base_url = str(request.base_url).rstrip("/")
    return_url = f"{base_url}/pay_success?{urlencode({'user_id': user_id, 'order_id': order_id})}"
    notify_url = f"{base_url}/payment_callback"
    provider = os.getenv("PAYMENT_PROVIDER", "personal").strip().lower()
    gateway_url = os.getenv("PAYMENT_GATEWAY_URL", "").strip()

    if provider == "personal":
        return f"{base_url}/manual_checkout?{urlencode({'order_id': order_id})}"

    if provider == "epay" and gateway_url:
        merchant_id = os.getenv("PAYMENT_MERCHANT_ID", "").strip()
        merchant_key = os.getenv("PAYMENT_MERCHANT_KEY", "").strip()
        if not merchant_id or not merchant_key:
            raise HTTPException(status_code=500, detail="缺少易支付商户ID或密钥配置")
        params = {
            "pid": merchant_id,
            "type": pay_type,
            "out_trade_no": order_id,
            "notify_url": notify_url,
            "return_url": return_url,
            "name": "小红书爆款标题AI Pro",
            "money": PRO_PRICE,
            "sitename": os.getenv("PAYMENT_SITE_NAME", "小红书爆款标题AI Pro"),
        }
        params["sign"] = build_epay_sign(params, merchant_key)
        params["sign_type"] = "MD5"
        separator = "&" if "?" in gateway_url else "?"
        return f"{gateway_url}{separator}{urlencode(params)}"

    if provider == "generic" and gateway_url:
        params = {
            "provider": "generic",
            "merchant_id": os.getenv("PAYMENT_MERCHANT_ID", ""),
            "order_id": order_id,
            "user_id": user_id,
            "pay_type": pay_type,
            "amount": PRO_PRICE,
            "name": "小红书爆款标题AI Pro",
            "return_url": return_url,
            "notify_url": notify_url,
        }
        secret = os.getenv("PAYMENT_NOTIFY_SECRET", "").strip()
        if secret:
            params["sign"] = build_generic_sign(params, secret)
        separator = "&" if "?" in gateway_url else "?"
        return f"{gateway_url}{separator}{urlencode(params)}"

    return f"{base_url}/checkout?{urlencode({'order_id': order_id})}"


def admin_key_is_valid(admin_key: str) -> bool:
    expected = os.getenv("ADMIN_SECRET", "").strip()
    return bool(expected) and hmac.compare_digest(admin_key, expected)


def payment_qr_url(pay_type: str) -> str:
    default_alipay = "https://raw.githubusercontent.com/yehuar129-jpg/xhs-title-ai/main/alipay.png"
    default_wxpay = "https://raw.githubusercontent.com/yehuar129-jpg/xhs-title-ai/main/wechat.png"
    if pay_type == "wxpay":
        return os.getenv("WXPAY_QR_URL", os.getenv("PERSONAL_PAY_QR_URL", default_wxpay)).strip()
    return os.getenv("ALIPAY_QR_URL", os.getenv("PERSONAL_PAY_QR_URL", default_alipay)).strip()


@app.get("/")
def home() -> FileResponse:
    return FileResponse(Path(__file__).with_name("index.html"))


@app.get("/user_status")
def user_status(user_id: str = Query(..., min_length=1)) -> Dict[str, object]:
    user = ensure_user(user_id)
    return {
        "user_id": user_id,
        "plan": user["plan"],
        "used_today": user["used_today"],
        "usage_left": usage_left(user),
    }


@app.post("/generate", response_model=GenerateResponse)
def generate_titles(payload: GenerateRequest) -> GenerateResponse:
    user = ensure_user(payload.user_id)
    is_pro = user["plan"] == "pro"

    if not is_pro:
        left = usage_left(user)
        if left <= 0:
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "今日免费次数已用完，升级 Pro 后可无限生成。",
                    "plan": "free",
                    "usage_left": 0,
                },
            )
        user["used_today"] = int(user["used_today"]) + 1

    return GenerateResponse(
        plan="pro" if is_pro else "free",
        usage_left=usage_left(user),
        titles=build_titles(payload.keyword, is_pro),
    )


@app.post("/create_order")
def create_order(payload: CreateOrderRequest, request: Request) -> Dict[str, str]:
    ensure_user(payload.user_id)
    order_id = uuid4().hex
    orders[order_id] = {
        "order_id": order_id,
        "user_id": payload.user_id,
        "amount": PRO_PRICE,
        "pay_type": payload.pay_type,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
    }
    return {
        "order_id": order_id,
        "pay_type": payload.pay_type,
        "pay_url": build_pay_url(request, payload.user_id, order_id, payload.pay_type),
    }


@app.get("/checkout", response_class=HTMLResponse)
def checkout(order_id: str) -> str:
    order = orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return f"""
    <!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>支付配置未完成</title></head>
    <body style="font-family:Arial,'Microsoft YaHei',sans-serif;padding:40px;color:#111827;line-height:1.8">
      <h1>还没有接入真实支付</h1>
      <p>订单已创建：{order_id}</p>
      <p>请先配置支付商户参数。未收到支付平台成功回调前，系统不会自动开通 Pro。</p>
      <p><a href="/" style="color:#b42318">返回首页</a></p>
    </body></html>
    """


@app.get("/manual_checkout", response_class=HTMLResponse)
def manual_checkout(order_id: str) -> str:
    order = orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    pay_type = str(order.get("pay_type", "alipay"))
    pay_name = "微信支付" if pay_type == "wxpay" else "支付宝"
    qr_url = payment_qr_url(pay_type)
    qr_block = (
        f'<img src="{qr_url}" alt="{pay_name}收款码" style="width:220px;max-width:100%;border:1px solid #e7e9f0;border-radius:8px;padding:8px;background:#fff">'
        if qr_url
        else '<div style="padding:28px;border:1px dashed #cfd4dc;border-radius:8px;color:#667085">还没有配置收款码图片地址</div>'
    )

    return f"""
    <!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>个人收款开通 Pro</title></head>
    <body style="font-family:Arial,'Microsoft YaHei',sans-serif;margin:0;background:#f7f8fb;color:#111827">
      <main style="max-width:720px;margin:40px auto;padding:24px;background:#fff;border:1px solid #e7e9f0;border-radius:8px">
        <h1 style="margin:0 0 12px">升级 Pro</h1>
        <p style="color:#667085;line-height:1.7">请使用 {pay_name} 扫码付款。付款备注请填写订单号，方便人工确认。</p>
        <div style="display:grid;grid-template-columns:260px 1fr;gap:20px;align-items:start;margin-top:22px">
          <div>{qr_block}</div>
          <div style="line-height:1.9">
            <p><strong>金额：</strong>¥{order["amount"]}</p>
            <p><strong>订单号：</strong><code>{order_id}</code></p>
            <p><strong>支付方式：</strong>{pay_name}</p>
            <p><strong>状态：</strong>{order["status"]}</p>
          </div>
        </div>
        <form method="post" action="/submit_payment_proof" style="margin-top:22px">
          <input type="hidden" name="order_id" value="{order_id}">
          <label>联系方式或备注<br><input name="contact" placeholder="例如微信号/手机号后四位/付款备注" style="width:100%;height:42px;margin-top:6px;padding:0 10px;border:1px solid #d0d5dd;border-radius:8px"></label>
          <label style="display:block;margin-top:12px">补充说明<br><input name="note" placeholder="可填写付款时间、昵称等" style="width:100%;height:42px;margin-top:6px;padding:0 10px;border:1px solid #d0d5dd;border-radius:8px"></label>
          <button style="width:100%;height:46px;margin-top:16px;border:0;border-radius:8px;background:#d92d20;color:#fff;font-weight:800">我已付款，提交确认</button>
        </form>
        <p style="margin-top:16px;color:#667085;font-size:14px">提交后请等待人工确认。确认到账后，Pro 会开通。</p>
        <p><a href="/" style="color:#b42318">返回首页</a></p>
      </main>
    </body></html>
    """


@app.post("/submit_payment_proof", response_class=HTMLResponse)
async def submit_payment_proof(request: Request) -> str:
    data = await read_callback_data(request)
    order_id = data.get("order_id", "")
    order = orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order["status"] == "pending":
        order["status"] = "reviewing"
    order["contact"] = data.get("contact", "")
    order["note"] = data.get("note", "")
    order["submitted_at"] = datetime.utcnow().isoformat()
    return f"""
    <!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>已提交付款确认</title></head>
    <body style="font-family:Arial,'Microsoft YaHei',sans-serif;padding:40px;color:#111827">
      <h1>已提交付款确认</h1>
      <p>订单号：<code>{order_id}</code></p>
      <p>人工确认到账后会开通 Pro。请稍后返回首页查看套餐状态。</p>
      <p><a href="/" style="color:#b42318">返回首页</a></p>
    </body></html>
    """


@app.get("/admin_orders", response_class=HTMLResponse)
def admin_orders(admin_key: str = "") -> str:
    if not admin_key_is_valid(admin_key):
        raise HTTPException(status_code=403, detail="管理员密钥错误")
    rows = []
    for order in reversed(list(orders.values())):
        order_id = str(order["order_id"])
        rows.append(
            "<tr>"
            f"<td><code>{order_id}</code></td>"
            f"<td>{order['user_id']}</td>"
            f"<td>¥{order['amount']}</td>"
            f"<td>{order.get('pay_type', '')}</td>"
            f"<td>{order['status']}</td>"
            f"<td>{order.get('contact', '')}</td>"
            f"<td>{order.get('note', '')}</td>"
            f"<td><a href='/admin_activate?admin_key={admin_key}&order_id={order_id}'>确认开通</a></td>"
            "</tr>"
        )
    body = "\n".join(rows) or "<tr><td colspan='8'>暂无订单</td></tr>"
    return f"""
    <!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>订单管理</title></head>
    <body style="font-family:Arial,'Microsoft YaHei',sans-serif;padding:24px;color:#111827">
      <h1>个人收款订单</h1>
      <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;width:100%">
        <thead><tr><th>订单号</th><th>用户</th><th>金额</th><th>方式</th><th>状态</th><th>联系方式</th><th>备注</th><th>操作</th></tr></thead>
        <tbody>{body}</tbody>
      </table>
    </body></html>
    """


@app.get("/admin_activate")
def admin_activate(order_id: str, admin_key: str = "") -> Dict[str, object]:
    if not admin_key_is_valid(admin_key):
        raise HTTPException(status_code=403, detail="管理员密钥错误")
    order = orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    user = mark_user_pro(str(order["user_id"]), order_id)
    return {"ok": True, "order_id": order_id, "user_id": order["user_id"], "plan": user["plan"]}


@app.get("/pay_success", response_class=HTMLResponse)
def pay_success(user_id: str, order_id: Optional[str] = None) -> str:
    if order_id and order_id in orders and orders[order_id]["user_id"] != user_id:
        raise HTTPException(status_code=400, detail="订单与用户不匹配")
    if not order_id or order_id not in orders or orders[order_id].get("status") != "paid":
        return """
        <!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <title>等待支付确认</title></head>
        <body style="font-family:Arial,'Microsoft YaHei',sans-serif;padding:40px;color:#111827">
          <h1>正在等待支付确认</h1>
          <p>支付平台回调成功后，Pro 会自动开通。请稍后回到首页刷新状态。</p>
          <p><a href="/" style="color:#b42318">返回首页</a></p>
        </body></html>
        """
    return """
    <!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>支付成功</title></head>
    <body style="font-family:Arial,'Microsoft YaHei',sans-serif;padding:40px;color:#111827">
      <h1>支付成功，Pro 已开通</h1>
      <p>正在返回小红书爆款标题AI Pro...</p>
      <script>setTimeout(function(){location.href='/?paid=success'},900)</script>
    </body></html>
    """


async def read_callback_data(request: Request) -> Dict[str, str]:
    data = dict(request.query_params)
    body = await request.body()
    if body:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            data.update(await request.json())
        else:
            parsed = parse_qs(body.decode("utf-8"))
            data.update({key: value[-1] for key, value in parsed.items() if value})
    return {key: str(value) for key, value in data.items()}


def apply_payment_callback(data: Dict[str, str]) -> Dict[str, object]:
    provider = os.getenv("PAYMENT_PROVIDER", "personal").strip().lower()
    if provider == "personal":
        raise HTTPException(status_code=400, detail="个人收款模式不接受自动支付回调")
    if provider == "epay":
        merchant_key = os.getenv("PAYMENT_MERCHANT_KEY", "").strip()
        if not merchant_key or data.get("sign") != build_epay_sign(data, merchant_key):
            raise HTTPException(status_code=400, detail="支付回调验签失败")
    elif provider == "generic":
        secret = os.getenv("PAYMENT_NOTIFY_SECRET", "").strip()
        if secret and data.get("sign") != build_generic_sign(data, secret):
            raise HTTPException(status_code=400, detail="支付回调验签失败")

    status = data.get("status") or data.get("trade_status") or data.get("result") or "success"
    paid_status = status.lower() in {"success", "paid", "trade_success", "ok"}
    order_id = data.get("order_id") or data.get("out_trade_no") or data.get("trade_no")
    order = orders.get(order_id or "") if order_id else None
    user_id = data.get("user_id") or (str(order["user_id"]) if order else None)

    if not paid_status or not user_id:
        raise HTTPException(status_code=400, detail="支付回调未成功或缺少用户信息")

    user = mark_user_pro(user_id, order_id)
    return {"ok": True, "plan": user["plan"], "user_id": user_id}


@app.post("/payment_callback")
async def payment_callback(request: Request) -> Dict[str, object]:
    return apply_payment_callback(await read_callback_data(request))


@app.get("/payment_callback")
async def payment_callback_get(request: Request) -> Dict[str, object]:
    return apply_payment_callback(await read_callback_data(request))
