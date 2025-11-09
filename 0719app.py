import pandas as pd
import random
import csv
import os
from datetime import datetime
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import re
import gspread

# --- Google Sheets Setup ---
# google-authライブラリを使用した認証方法
from google.oauth2.service_account import Credentials
# --- Google Sheets Setup ---
# google-authライブラリを使用した認証方法
from google.oauth2.service_account import Credentials

# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ★★★ credentials.json の内容をここに埋め込んでください ★★★
# Google Cloud Console から service account の JSON キーをコピーして、下記の辞書に置き換えてください
CREDENTIALS_DICT = {
    "type": "service_account",
    "project_id": "gen-lang-client-0722953733",
    "private_key_id": "03be7933595c1e2f3894b8355eb5ff5ba7e0cc44",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCYMShJcm4AugT/\n48+HnaKV5z+fYUbmqTmttk+K7buqpArRDojwO/pqDZSuUmA8Df2leNThecWUWobM\nG5W6o7NtdkcZnZRErXsA6Eql4U3TZJX5mVRUhhF4GgBBoxI5dA7v/h0Cw/SkDx+8\n8c6LNQOX3JNnJ26qpTBFzjPIwpCWDjf3iogalcjaQClddhWreDjKdDIiLuD3bDYU\ntoC/oQtfjIyqhugZsxKriauqNBJP6u7fcrILxGzXxCgB+OI9E8V6ERPgqlMoCoeh\nbDyARDSgKen3VWMEqipbAgsz7QWCBkhNX3+6+FY7ctSSt0aO3ODf+R1nIh4MNNSB\n5i5hiL1TAgMBAAECggEAHJDVe/uzdAV2XMVYtZ673qEaCwNKOI842Ucn5O68U8oY\nkabFwzmuxesophOmJn+FxWJJqsydbjwTownmb7K8QeZ6b+9o3f8l4ES5hisk3XG6\nyK+j6X2El+NhevBtwkTrbNZogZVgPM7t6RwF5ZEczItFS45WMkdxKRkMFTmXw+I7\nO9wKh74hKFwhzYWuYaIHsYl33EhdEgkfBd/YelqaVCzqcJ0spD7iZ2I1hhcbG8Xe\nrb3FgVL5IXjgayjbdLlDtQSbyzl6G0C9ifHQZ1t5fmSMZV0ioZW1ouuPVONdx/u1\nwFOMSyQrqlatuuY398nUwYHnK9iuVWsM2rG8cOy+YQKBgQDF9jScO4ROQuekUfOm\n8VK+IAWxC6LtLvg6Mp+vF8bNjmUU9KksxkNJr+1rnd269K87o2zoJS1K1mkFKb5A\n4GylT1xZ0stPlloq+j60oZJjtzrz3RwCB4tI3OLLAfiLVxBMewLIdDI9uDAEiZ6K\n0h2rZ7ujO661+zIkYJyQzYURgwKBgQDEz8Hh4uzqW8xvczPEi+UlA/ARNizbp4aL\n4HKhk889J9lZld3J8pHhniz0BKpk3Y3ak3ELiaMXAfWZl9/r+q3RY946e/pqYfNw\n7gh1YslbVCcICyqfraKXTtsBVexYzMzdtP29sVwWQSg2337ww65nHlJQ5/Z48T6T\nylNaOBDr8QKBgGCIXMNKqovXSEnyxJPF3glkaCIbgImUe+s1QHULbSBTrar4W36/\n95P5PBdcVgGSy9iTKspRRrLVt0STRHkydwhtmKUci5P1x2ZpvSYsG8yQTykXy06a\nCyuuutEv1tlrzUDeQ08oik9af9/Wk/8x0tIAtZk1w05ufdcLXY2nCpqtAoGALk3f\nBME6Ek10xMfq5xQu3k2V3sbLOQaqHiC5d5BqEq5ccbpTyx6Z+eYYF3U9jaueo01L\nLHa+ezxHx1I3KbL50CjZ8RKYMQ1IlEo8jTmnvCgJYtgVuCnG9ihkWGUZzS6qCIN7\nq3SeANJlnrtoh0bSsoosvcJFd+DyYx0YDULhoFECgYASz0PX/Cfp8s2l7nPA8x9Z\nxrDouFPScilga1DxeTxo41qd4CSxMevXe/Ev5apCWCn29ZGecy3ttZEir9PLa4AI\nt1zBLaVrH1RdvsWNeA5FpMxcerkTuXCEYJJXpxvtRw9+wr83/JiRh+xltR4sZKBJ\nzXzjty2RDeUF5YuxEt/50A==\n-----END PRIVATE KEY-----\n",
    "client_email": "experiments@gen-lang-client-0722953733.iam.gserviceaccount.com",
    "client_id": "116451437213176371171",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/experiments%40gen-lang-client-0722953733.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★

try:
    # APIへのアクセス権限（スコープ）を定義
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # credentials.jsonから認証情報を読み込む
    creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    
    # 認証情報を使ってgspreadクライアントを初期化
    client = gspread.authorize(creds)

    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    # ★★★ ここに、あなたが作成したGoogleスプレッドシートの「ファイル名」を正確に入力してください ★★★
    SPREADSHEET_NAME = "Twitter Stress Results"
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    
    # スプレッドシートを開き、最初のシートを選択
    sheet = client.open(SPREADSHEET_NAME).sheet1
    
    print("Googleスプレッドシートへの接続に成功しました。")

except gspread.exceptions.SpreadsheetNotFound:
    print(f"エラー: スプレッドシート '{SPREADSHEET_NAME}' が見つかりません。")
    print("1. スプレッドシート名が正しいか確認してください。")
    print(f"2. サービスアカウントのメールアドレスにスプレッドシートが共有されているか確認してください。")
    sheet = None
except Exception as e:
    print(f"Googleスプレッドシートへの接続中に予期せぬエラーが発生しました: {e}")
    print("続行しますが、データはCSVにのみ保存されます。")
    sheet = None

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app)

# --- Helper Function ---
def clean_text_line(text):
    """Removes potential prefixes like usernames or list markers from a string."""
    if not isinstance(text, str):
        return ""
    cleaned = re.sub(r'^\s*([A-Za-z0-9_]+:|@\w+\s*:|\s*[-\*\d\.]+\s*)', '', text)
    return cleaned.strip().strip('「」')

# --- Main Simulator Class ---
class TwitterSimulator:
    def __init__(self, low_stress_file, mid_stress_file, high_stress_file):
        """
        Initializes the simulator by loading tweet data from CSV files.
        """
        self.P_LOW = 0.0
        self.P_MID = 0.44
        self.P_HIGH = 0.74

        try:
            self.df_low = pd.read_csv(low_stress_file, on_bad_lines='skip', engine='python')
            self.low_tweets = self.df_low['text'].dropna().tolist()
            print(f"Successfully loaded {len(self.low_tweets)} low-stress tweets from {low_stress_file}")

            self.df_mid = pd.read_csv(mid_stress_file, on_bad_lines='skip', engine='python')
            self.mid_tweets = self.df_mid['text'].dropna().tolist()
            print(f"Successfully loaded {len(self.mid_tweets)} mid-stress tweets from {mid_stress_file}")

            self.df_high = pd.read_csv(high_stress_file, on_bad_lines='skip', engine='python')
            self.high_tweets = self.df_high['text'].dropna().tolist()
            print(f"Successfully loaded {len(self.high_tweets)} high-stress tweets from {high_stress_file}")

        except FileNotFoundError as e:
            print(f"FATAL ERROR: Data file not found: {e}. Make sure all CSV files are in the same directory as app.py.")
            exit()
        except KeyError as e:
            print(f"FATAL ERROR: A required column is missing from a CSV file: {e}")
            exit()

    def _calculate_counts(self, p, n):
        """
        Calculates the number of tweets to draw from each category to achieve the target probability 'p'.
        """
        # p = 0 の場合は Low のみ
        if p <= 0:
            return n, 0, 0
        
        # p = 1 の場合は High のみ
        if p >= 1:
            return 0, 0, n
        
        # p が P_MID 以下の場合：Low と Mid で構成
        if p <= self.P_MID:
            if self.P_MID > 0:
                ratio = p / self.P_MID
                n_mid = round(n * ratio)
                n_low = n - n_mid
                n_high = 0
            else:
                n_low = n
                n_mid = 0
                n_high = 0
        # p が P_MID より大きい場合：Mid と High で構成
        else:
            if self.P_HIGH > self.P_MID:
                ratio = (p - self.P_MID) / (self.P_HIGH - self.P_MID)
                n_high = round(n * ratio)
                n_mid = n - n_high
                n_low = 0
            else:
                n_high = n
                n_mid = 0
                n_low = 0

        # 負の値を避ける
        n_low = max(0, n_low)
        n_mid = max(0, n_mid)
        n_high = max(0, n_high)
        
        return int(n_low), int(n_mid), int(n_high)

    def create_timeline(self, target_probability, total_tweets=100):
        """
        Generates a timeline of tweets with a specific stress density.
        """
        n_low, n_mid, n_high = self._calculate_counts(target_probability, total_tweets)
        
        low_samples = random.choices(self.low_tweets, k=n_low) if n_low > 0 else []
        mid_samples = random.choices(self.mid_tweets, k=n_mid) if n_mid > 0 else []
        high_samples = random.choices(self.high_tweets, k=n_high) if n_high > 0 else []

        timeline = []
        timeline.extend([{'text': clean_text_line(t), 'source': 'Low Stress', 'stress': self.P_LOW} for t in low_samples])
        timeline.extend([{'text': clean_text_line(t), 'source': 'Mid Stress', 'stress': self.P_MID} for t in mid_samples])
        timeline.extend([{'text': clean_text_line(t), 'source': 'High Stress', 'stress': self.P_HIGH} for t in high_samples])

        random.shuffle(timeline)

        actual_stress_points = sum(t['stress'] for t in timeline)
        actual_prob = actual_stress_points / len(timeline) if timeline else 0
        
        return timeline, actual_prob

# --- Flask App Setup ---
simulator = TwitterSimulator(
    low_stress_file='wrime-ver1_converted.csv',
    mid_stress_file='all_merged.csv',
    high_stress_file='output.csv'
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/timeline', methods=['GET'])
def get_timeline():
    try:
        probability_percent = float(request.args.get('probability', '25'))
        target_probability = probability_percent / 100.0
        timeline, actual_prob = simulator.create_timeline(target_probability=target_probability, total_tweets=100)
        
        return jsonify({
            'success': True, 
            'timeline': timeline, 
            'target_probability': target_probability, 
            'actual_probability': actual_prob
        })
    except Exception as e:
        print(f"APIエラー: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/save_survey', methods=['POST'])
def save_survey():
    data = request.get_json()
    try:
        # CSVファイルに保存するデータ
        row_data_csv = [
            data.get('sessionId'), 
            data.get('targetProbability'), 
            data.get('actualProbability'), 
            data.get('interval'), 
            data.get('stressLevel'), 
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]
        
        # Googleスプレッドシートに保存するデータ
        row_data_gsheet = [
            data.get('sessionId'), 
            data.get('userName'),
            data.get('targetProbability'), 
            data.get('actualProbability'), 
            data.get('interval'), 
            data.get('stressLevel'), 
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]

        # --- 1. CSVファイルへの保存 ---
        filename = "survey_results.csv"
        file_exists = os.path.isfile(filename)
        
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                # CSVのヘッダーを修正
                writer.writerow(['session_id', 'user_name', 'target_probability', 'actual_probability', 'survey_interval_min', 'stress_level_vas', 'timestamp'])
            
            writer.writerow(row_data_gsheet) # Google Sheetと同じデータを書き込む
        
        print(f"アンケート結果をCSVに保存しました: {data}")

        # --- 2. Googleスプレッドシートへの保存 ---
        if sheet:
            try:
                sheet.append_row(row_data_gsheet, value_input_option='USER_ENTERED')
                print(f"アンケート結果をGoogleスプレッドシートに保存しました。")
            except Exception as e:
                print(f"Googleスプレッドシートへの書き込みエラー: {e}")

        return jsonify({'success': True, 'message': 'Result saved.'})
    except Exception as e:
        print(f"アンケート保存エラー: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)