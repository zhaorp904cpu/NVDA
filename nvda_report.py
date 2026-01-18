import os
import sys
import datetime
import smtplib
import requests
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

DS_KEY = os.getenv("DEEPSEEK_API_KEY")
MY_PASS = os.getenv("EMAIL_PASS")
MY_MAIL = os.getenv("MY_MAIL")


def get_nvda_intelligence():
    if not DS_KEY:
        return "未配置 DEEPSEEK_API_KEY，以下盈利预测基于固定假设，请结合你自己的行业跟踪结论进行修正。"
    prompt = (
        "你是一名长期跟踪 NVIDIA (NVDA) 的卖方分析师，正在撰写一份“未来四个尚未公布季度业绩预测”的内部备忘录。"
        "请基于最近一周公开信息，从以下角度进行分析："
        "1）供应链：TSMC CoWoS 产能、HBM3/3E/4 供应、GPU 晶圆投片节奏是否有新的瓶颈或扩产计划；"
        "2）需求侧：北美云厂商(AWS/Azure/GCP/Meta)、中国云厂、超算/企业客户的 AI CapEx 指引或实际订单是否有上调/下调；"
        "3）产品与竞争：H100/H200/B100/B200 的生命周期位置、价格体系变化，以及 AMD/自研 ASIC 对份额和定价的边际影响；"
        "4）你的结论：相对于此前基准预期，未来四个尚未公布季度的营收增速应是上修、下修还是大致持平，主要驱动是什么。"
        "请用简洁中文分点输出，不要给出具体数字，只给定性结论和风险提示。"
    )
    try:
        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {DS_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "deepseek-reasoner",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code != 200:
            return f"情报获取失败: HTTP {resp.status_code}: {resp.text}"
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"情报获取失败: {e}"


def get_forecast_assumptions():
    last_rev = 42.0
    last_net = 25.1

    base_rev_growth = [0.10, 0.08, 0.07, 0.07]

    cowos_impact = [-0.03, -0.01, 0.00, 0.00]

    hbm_impact = [0.00, 0.00, 0.02, 0.02]

    capex_impact = [0.02, 0.02, 0.01, 0.00]

    net_leverage = 0.02

    quarters = ["FY26 Q4E", "FY27 Q1E", "FY27 Q2E", "FY27 Q3E"]

    return {
        "last_rev": last_rev,
        "last_net": last_net,
        "base_rev_growth": base_rev_growth,
        "cowos_impact": cowos_impact,
        "hbm_impact": hbm_impact,
        "capex_impact": capex_impact,
        "net_leverage": net_leverage,
        "quarters": quarters,
    }


def build_forecast():
    a = get_forecast_assumptions()

    rev_growth = []
    net_growth = []
    forecast = []

    prev_rev = a["last_rev"]
    prev_net = a["last_net"]

    for i in range(4):
        g_rev = (
            a["base_rev_growth"][i]
            + a["cowos_impact"][i]
            + a["hbm_impact"][i]
            + a["capex_impact"][i]
        )
        rev_growth.append(g_rev)
        g_net = g_rev + a["net_leverage"]
        net_growth.append(g_net)

        r = prev_rev * (1 + g_rev)
        n = prev_net * (1 + g_net)

        forecast.append(
            {
                "quarter": a["quarters"][i],
                "revenue": round(r, 1),
                "net_income": round(n, 1),
                "rev_growth": g_rev,
                "net_growth": g_net,
            }
        )

        prev_rev = r
        prev_net = n

    return forecast, a


def format_growth_list(values):
    return ", ".join(f"{v * 100:.0f}%" for v in values)


def format_pp_list(values):
    return ", ".join(f"{v * 100:.0f}pp" for v in values)


def send_mail(intel, forecast, assumptions):
    if not MY_PASS or not MY_MAIL:
        print("未检测到 EMAIL_PASS 或 MY_MAIL，跳过发送邮件。")
        return

    intel_html = intel.replace("\n", "<br>")

    table_rows = ""
    for item in forecast:
        table_rows += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{item['quarter']}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">${item['revenue']} B</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right; font-weight: bold;">${item['net_income']} B</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center; color: #e74c3c;">{item['rev_growth'] * 100:.0f}%</td>
        </tr>
        """

    base_rev_str = format_growth_list(assumptions["base_rev_growth"])
    cowos_str = format_pp_list(assumptions["cowos_impact"])
    hbm_str = format_pp_list(assumptions["hbm_impact"])
    capex_str = format_pp_list(assumptions["capex_impact"])
    last_rev = assumptions["last_rev"]
    last_net = assumptions["last_net"]
    net_leverage = assumptions["net_leverage"] * 100

    html = f"""
    <html>
    <body style="font-family: '微软雅黑', sans-serif; max-width: 900px; margin: 0 auto; color: #333;">
        <h2 style="color: #76b900; border-bottom: 2px solid #76b900; padding-bottom: 10px;">
            NVIDIA (NVDA) 未来四个尚未公布季度业绩前瞻周报
        </h2>
        <p style="color: #666; font-size: 14px;"><b>生成日期：</b> {datetime.date.today()}</p>

        <h3>📊 未来四个季度盈利预测（自最近已公布季度之后起算）</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px;">
            <thead>
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 10px; border: 1px solid #ddd;">财年季度</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">预测营收 (Revenue)</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">预测净利 (Net Income)</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">营收环比增速</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        <p style="font-size: 12px; color: #888; margin-top: 4px;">
            单位：十亿美元 ($B)。预测区间覆盖自 2026 Q4E 起的未来四个尚未公布季度。
        </p>

        <h3>🧩 关键建模假设拆解</h3>
        <div style="background-color: #f9f9f9; padding: 15px; border-left: 5px solid #76b900; line-height: 1.7; font-size: 14px;">
            <p><b>1. 起点基准：</b>以最近一个已公布季度为起点，实际营收约 {last_rev:.1f} B，实际净利润约 {last_net:.1f} B。</p>
            <p><b>2. 基准路径（不考虑新事件时）：</b>未来四个季度营收环比基准假设为 [{base_rev_str}]。</p>
            <p><b>3. 供应链冲击：</b>CoWoS 产能对营收增速的季度影响向量为 [{cowos_str}]；HBM 供应变化对营收增速的影响向量为 [{hbm_str}]。</p>
            <p><b>4. 需求与 CapEx 冲击：</b>云厂商 AI CapEx 调整对营收增速的影响向量为 [{capex_str}]。</p>
            <p><b>5. 利润弹性：</b>净利润环比增速相对于营收增速附加约 {net_leverage:.0f} 个百分点，以反映毛利率与运营杠杆的放大效应。</p>
        </div>

        <h3>🔍 DeepSeek 模型情报摘要</h3>
        <div style="background-color: #fdfdfd; padding: 15px; border: 1px solid #eee; line-height: 1.7; font-size: 14px;">
            {intel_html}
        </div>

        <hr style="margin-top: 30px; border: 0; border-top: 1px solid #eee;">
        <p style="text-align: center; font-size: 12px; color: #aaa;">
            本报告为内部模型推演结果，仅供参考，不构成任何投资建议。<br>
            建议在每次重大供应链或 CapEx 事件后，及时调整上述冲击向量并重新生成本报表。
        </p>
    </body>
    </html>
    """

    msg = MIMEText(html, "html", "utf-8")
    msg["From"] = formataddr((str(Header("NVDA业绩哨兵", "utf-8")), MY_MAIL))
    msg["To"] = MY_MAIL
    msg["Subject"] = Header(
        f"【AI前瞻】NVDA 未来四季度盈利预测周报 - {datetime.date.today()}",
        "utf-8",
    )

    try:
        with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
            server.login(MY_MAIL, MY_PASS)
            server.sendmail(MY_MAIL, [MY_MAIL], msg.as_bytes())
        print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败: {e}")


def main():
    intel = get_nvda_intelligence()
    forecast, assumptions = build_forecast()
    send_mail(intel, forecast, assumptions)


if __name__ == "__main__":
    main()
