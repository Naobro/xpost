import streamlit as st
import pandas as pd
import os
import tweepy
from config import API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, CSV_FILE

st.title("🐦 手動ツイート管理ツール")

# ✅ CSVを読み込む（列が足りない場合は追加）
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=["title", "category", "tweet_text", "script", "thumbnail_url", "posted"])

# ✅ 必須列を追加（存在しなければ）
required_cols = ["title", "category", "tweet_text", "script", "thumbnail_url", "posted"]
for col in required_cols:
    if col not in df.columns:
        df[col] = "" if col != "posted" else False

# ✅ 未投稿・投稿済みを分けて表示
tab1, tab2 = st.tabs(["⏳ 未投稿リスト", "✅ 投稿済みリスト"])
with tab1:
    st.subheader("未投稿リスト")
    st.dataframe(df[df["posted"] == False])

with tab2:
    st.subheader("投稿済みリスト")
    st.dataframe(df[df["posted"] == True])

# ✅ ツイート対象の選択
video_titles = df[df["posted"] == False]["title"].tolist()
if video_titles:
    selected_title = st.selectbox("ツイートする広告を選択", video_titles)
    tweet_button = st.button("🐦 ツイートする")
else:
    st.info("未投稿の広告がありません。")
    selected_title = None
    tweet_button = False

# ✅ Twitter API認証
def get_twitter_api():
    auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    return tweepy.API(auth)

# ✅ ツイート送信
def post_tweet(api, text, url, thumbnail=None):
    tweet_text = f"{text}\n\n詳細はこちら👇\n{url}"
    try:
        api.update_status(tweet_text)
        return True
    except Exception as e:
        st.error(f"❌ ツイート失敗: {e}")
        return False

# ✅ ボタンが押されたらツイート
if tweet_button and selected_title:
    row = df[df["title"] == selected_title].iloc[0]

    api = get_twitter_api()
    success = post_tweet(api, row["tweet_text"], row["script"], row.get("thumbnail_url", ""))

    if success:
        st.success(f"✅ ツイートしました: {selected_title}")
        df.loc[df["title"] == selected_title, "posted"] = True
        df.to_csv(CSV_FILE, index=False)
        st.rerun()