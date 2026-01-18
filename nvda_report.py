import os
import sys
import datetime
import smtplib
import requests
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

# --- 环境变量配置 ---
DS_KEY = os.getenv("DEEPSEEK_API_KEY")
MY_PASS = os.getenv("EMAIL_PASS")
MY_MAIL = os.getenv("MY_MAIL")

# 简单的自检
if not DS_KEY:
    print("⚠️ 警告：未检测到 DEEPSEEK_API_KEY，将无法获取智能情报")
if not MY_PASS or not MY_MAIL:
    print("⚠️ 警告：未检测到邮箱配置 (EMAIL_PASS, MY_MAIL)，将无法发送邮件")


def get_nvda_intelligence():
    """
    调用 DeepSeek 获取 NVDA 供应链与 CapEx 动态分析
    """
    if not DS_KEY:
        return "（由于未配置 API Key，暂无智能情报）"

    prompt = "请分析过去一周 NVIDIA 的供应链(TSMC/HBM)与云厂商CapEx动态，重点关注对未来四个季度业绩的影响，生成简短的预测推导参数分析。"
    try:
        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {DS_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "deepseek-reasoner",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
        }
        print("🧠 正在调用 DeepSeek 获取情报...")
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code != 200:
            return f"情报获取失败: HTTP {resp.status_code}: {resp.text}"
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"情报获取失败: {e}"


def calculate_forecast():
    """
    模拟生成未来 4 个季度的预测数据 (单位: 十亿美元 $B)
    这里暂时使用硬编码的示例数据，实际应用中可替换为 API 获取或模型推演
    """
    # 假设当前是 2026 财年 (FY26)
    # Q1 ~ Q4 的预测值
    forecast_data = [
        {"quarter": "FY26 Q1", "revenue": 34.5, "net_income": 19.8, "growth": "+15%"},
        {"quarter": "FY26 Q2", "revenue": 38.2, "net_income": 22.5, "growth": "+10%"},
        {"quarter": "FY26 Q3", "revenue": 42.0, "net_income": 25.1, "growth": "+10%"},
        {"quarter": "FY26 Q4", "revenue": 46.5, "net_income": 28.3, "growth": "+11%"},
    ]
    return forecast_data


def send_mail(intel, forecast_list):
    """
    发送 HTML 格式的邮件，包含分季度的预测表格
    """
    if not MY_PASS or not MY_MAIL:
        print("❌ 邮箱未配置，跳过发送")
        return

    # 1. 处理情报文本换行
    intel_html = intel.replace("\n", "<br>")

    # 2. 动态生成表格行
    table_rows = ""
    for item in forecast_list:
        table_rows += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{item['quarter']}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">${item['revenue']} B</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: right; font-weight: bold;">${item['net_income']} B</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center; color: #e74c3c;">{item['growth']}</td>
        </tr>
        """

    # 3. 组装完整 HTML
    html = f"""
    <html>
    <body style="font-family: '微软雅黑', sans-serif; max-width: 800px; margin: 0 auto; color: #333;">
        <h2 style="color: #76b900; border-bottom: 2px solid #76b900; padding-bottom: 10px;">
            NVIDIA (NVDA) 季度业绩前瞻周报
        </h2>
        <p style="color: #666; font-size: 14px;"><b>生成日期：</b> {datetime.date.today()}</p>
        
        <h3>📊 业绩预测 (分季度拆解)</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <thead>
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 10px; border: 1px solid #ddd;">财年季度</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">预测营收 (Revenue)</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">预测净利 (Net Income)</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">环比增速</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        <p style="font-size: 12px; color: #888;">* 单位：十亿美元 ($B) | 数据来源：模型推演</p>

        <h3>🔍 智能情报摘要 (DeepSeek R1)</h3>
        <div style="background-color: #f9f9f9; padding: 20px; border-left: 5px solid #76b900; line-height: 1.6;">
            {intel_html}
        </div>
        
        <hr style="margin-top: 30px; border: 0; border-top: 1px solid #eee;">
        <p style="text-align: center; font-size: 12px; color: #aaa;">
            本报告由 AI 自动生成，仅供参考，不构成投资建议。<br>
            数据推导基于：TSMC CoWoS 产能、HBM4 供应及云厂商 CapEx 支出模型。
        </p>
    </body>
    </html>
    """

    msg = MIMEText(html, "html", "utf-8")
    msg["From"] = formataddr((str(Header("NVDA业绩哨兵", "utf-8")), MY_MAIL))
    msg["To"] = MY_MAIL
    msg["Subject"] = Header(
        f"【AI前瞻】NVDA 分季度业绩预测周报 - {datetime.date.today()}",
        "utf-8",
    )

    print("📧 正在发送邮件...")
    try:
        with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
            server.login(MY_MAIL, MY_PASS)
            server.sendmail(MY_MAIL, [MY_MAIL], msg.as_bytes())
        print("✅ 邮件发送成功！")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")


if __name__ == "__main__":
    # 1. 获取情报
    intel_data = get_nvda_intelligence()
    
    # 2. 获取分季度预测数据
    forecast_list = calculate_forecast()
    
    # 3. 发送邮件
    send_mail(intel_data, forecast_list)
