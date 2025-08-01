import pandas as pd
import tweepy
import time
from datetime import datetime
from config import API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, CSV_FILE

def tweet_video():
    df = pd.read_csv(CSV_FILE)
    if df.empty:
        print("⚠️ CSVが空です。ツイート対象なし。")
        return

    row = df.iloc[0]
    text = f"{row['title']}\n\n{row['tweet_text']}\n\n{row['video_url']}"

    auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    try:
        api.update_status(status=text)
        print(f"✅ ツイート成功: {row['title']}")

        df = df.drop(index=0)
        df.to_csv(CSV_FILE, index=False)
        print("✅ CSVから削除しました")
    except Exception as e:
        print(f"❌ ツイート失敗: {e}")

# =========================
# 23時になるまで待機 → ツイート実行
# =========================
while True:
    now = datetime.now().strftime("%H:%M")
    if now == "23:00":
        tweet_video()
        time.sleep(60)  # 1分待って次ループ
    else:
        time.sleep(30)