import pandas as pd
import requests
import io
import time
from datetime import datetime

# 설정 정보 (본인의 토큰과 ID로 확인하세요)
TOKEN = '8769926264:AAEHwxRM9II5MMFoB1msyd8byBJ9tAYN-Dc'
CHAT_ID = '1325771291'

# 관심 종목 리스트
target_stocks = [
    ('005930', '삼성전자'), ('000660', 'SK하이닉스'), 
    ('005380', '현대차'), ('035420', 'NAVER'),
    ('068270', '셀트리온'), ('005490', 'POSCO홀딩스')
]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    try:
        requests.get(url)
    except Exception as e:
        print(f"전송 오류: {e}")

def get_stock_data(code):
    url = f"https://finance.naver.com/item/frgn.naver?code={code}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers)
    try:
        tables = pd.read_html(io.StringIO(res.text))
        for table in tables:
            if '외국인' in str(table.columns) or '외국인' in table.to_string():
                table.columns = ['날짜', '종가', '전일비', '등락률', '거래량', '기관', '외국인', '보유주수', '보유율']
                table = table.iloc[1:]
                table['기관'] = pd.to_numeric(table['기관'], errors='coerce')
                table['외국인'] = pd.to_numeric(table['외국인'], errors='coerce')
                # 등락률 정제 (숫자형 변환)
                table['등락률_num'] = table['등락률'].replace({'%': '', '\+': ''}, regex=True).astype(float)
                return table
    except: return None
    return None

def check_surge(df):
    if df is None: return False
    # [기준] 최근 5일 수급 합계가 20일 평균의 4배 이상 & 최근 5일 평균 등락률이 양수
    recent_5d = df[['기관', '외국인']].head(5).sum().sum()
    avg_20d = df[['기관', '외국인']].head(20).mean().sum()
    is_volume_strong = recent_5d > (avg_20d * 4) 
    is_price_up = df['등락률_num'].head(5).mean() > 0
    return is_volume_strong and is_price_up

def generate_report():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 분석 시작...")
    report_msg = "📊 [수급 정기 보고서]\n"
    
    for code, name in target_stocks:
        df = get_stock_data(code)
        if df is not None:
            total = df[['기관', '외국인']].head(20).sum().sum()
            status = "🚨급증(주도주)" if check_surge(df) else "정상"
            report_msg += f"- {name}: {total:,.0f}주 ({status})\n"
        time.sleep(1) # 서버 보호
        
    send_telegram_message(report_msg)
    print("보고서 발송 완료!")

# 실행
if __name__ == "__main__":
    generate_report()