import os
import sys
import datetime
import smtplib
# 核心修复：必须从 email 库中导入这些具体的组件
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from google import genai

# 获取环境变量
MY_KEY = os.getenv("GEMINI_API_KEY")
MY_PASS = os.getenv("EMAIL_PASS")
MY_MAIL = os.getenv("MY_MAIL")

# 诊断信息（确认变量已送达）
print(f"DEBUG: 环境变量检测:")
print(f"GEMINI_API_KEY: {'Yes' if MY_KEY else 'No'}")
print(f"EMAIL_PASS: {'Yes' if MY_PASS else 'No'}")
print(f"MY_MAIL: {'Yes' if MY_MAIL else 'No'}")

if not MY_KEY:
    print("❌ 错误：未检测到 API Key，请检查 GitHub Secrets")
    sys.exit(1)

client = genai.Client(api_key=MY_KEY)

# --- 以下是你原来的函数部分 ---

def get_nvda_intelligence():
    prompt = "请分析过去一周 NVIDIA 的供应链(TSMC/HBM)与云厂商CapEx动态，生成预测推导参数。"
    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        return f"情报获取失败: {e}"

def calculate_forecast():
    # 模拟推导模型逻辑（可根据需求后期接入实时数据）
    return {"Revenue": 68.5, "Net_Income": 34.2}

def send_mail(intel, res):
    # 构造 HTML 邮件内容
    html = f"""
    <html>
    <body>
        <h2 style="color: #76b900;">NVIDIA (NVDA) 业绩前瞻周报</h2>
        <p><b>生成日期：</b> {datetime.date.today()}</p>
        <hr>
        <h3>📊 核心预测</h3>
        <ul>
            <li>预测营收: <b>${res['Revenue']}B</b></li>
            <li>预测净利润: <b>${res['Net_Income']}B</b></li>
        </ul>
        <h3>🔍 智能情报摘要</h3>
        <p>{intel.replace('\\n', '<br>')}</p>
    </body>
    </html>
    """
    msg = MIMEText(html, 'html', 'utf-8')
    msg['From'] = formataddr((str(Header("NVDA业绩哨兵", 'utf-8')), MY_MAIL))
    msg['To'] = MY_MAIL
    msg['Subject'] = Header(f"【AI前瞻】NVDA 季度业绩预测周报 - {datetime.date.today()}", 'utf-8')
    
    try:
        with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
            server.login(MY_MAIL, MY_PASS)
            server.sendmail(MY_MAIL, [MY_MAIL], msg.as_bytes())
        print("✅ 邮件发送成功！")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

if __name__ == "__main__":
    intel_data = get_nvda_intelligence()
    calc_res = calculate_forecast()
    send_mail(intel_data, calc_res)
