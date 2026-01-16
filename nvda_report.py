import os
import sys
from google import genai

# 获取环境变量
MY_KEY = os.getenv("GEMINI_API_KEY")
MY_PASS = os.getenv("EMAIL_PASS")
MY_MAIL = os.getenv("MY_MAIL")

# --- 强制诊断模块 ---
print(f"DEBUG: 操作系统环境中的变量检测:")
print(f"GEMINI_API_KEY 是否存在: {'Yes' if MY_KEY else 'No'}")
print(f"EMAIL_PASS 是否存在: {'Yes' if MY_PASS else 'No'}")
print(f"MY_MAIL 是否存在: {'Yes' if MY_MAIL else 'No'}")

if not MY_KEY:
    print("❌ 致命错误: 无法获取 GEMINI_API_KEY。请检查 GitHub Secrets 配置。")
    sys.exit(1)
# ------------------

client = genai.Client(api_key=MY_KEY)


def get_nvda_intelligence():
    prompt = "今天是 2026 年 1 月 15 日。请分析过去一周 NVIDIA 的供应链(TSMC/HBM)与云厂商(Microsoft/Meta)CapEx动态，生成财务推导参数。"
    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        return f"情报获取失败: {e}"

def calculate_forecast():
    # 模拟推导模型逻辑
    predicted_rev = 68.5  # 假设推导值
    predicted_net_income = 34.2
    return {"Revenue": predicted_rev, "Net_Income": predicted_net_income}

def send_mail(intel, res):
    html = f"<h2>NVDA 业绩前瞻周报</h2><p>{intel}</p><p>预测营收: ${res['Revenue']}B</p>"
    msg = MIMEText(html, 'html', 'utf-8')
    msg['From'] = formataddr((str(Header("NVDA哨兵", 'utf-8')), MY_MAIL))
    msg['To'] = MY_MAIL
    msg['Subject'] = Header(f"【GitHub自动送达】NVDA前瞻报告 - {datetime.date.today()}", 'utf-8')
    
    with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
        server.login(MY_MAIL, MY_PASS)
        server.sendmail(MY_MAIL, [MY_MAIL], msg.as_bytes())

if __name__ == "__main__":
    intel_data = get_nvda_intelligence()
    calc_res = calculate_forecast()
    send_mail(intel_data, calc_res)
