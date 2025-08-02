import streamlit as st
import pandas as pd
import os
import tweepy
from config import API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, CSV_FILE

st.title("🐦 手動ツイート管理ツール")

# ✅ CSV読み込み
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    st.error("CSVファイルが見つかりません。まず add_video.py で登録してください。")
    st.stop()

if "posted" not in df.columns:
    df["posted"] = False

# ✅ Twitter API 認証
def get_twitter_api():
    auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    return tweepy.API(auth)

# ✅ ツイート送信
def post_tweet(api, text, video_url, tags):
    try:
        tags_text = " ".join([f"#{tag}" for tag in tags.split(", ") if tag])
        tweet_text = f"{text}\n\n{video_url}\n\n{tags_text}".strip()
        api.update_status(tweet_text)
        return True
    except Exception as e:
        st.error(f"❌ ツイート失敗: {e}")
        return False

# ✅ 表示用タブ
tab1, tab2 = st.tabs(["⏳ 未投稿リスト", "✅ 投稿済みリスト"])

with tab1:
    st.subheader("⏳ 未投稿リスト")

    api = get_twitter_api()

    for i, row in df[df["posted"] == False].iterrows():
        st.markdown(f"### 🎬 {row['title']}")
        st.write(f"📝 {row['tweet_text']}")
        st.write(f"🔗 {row['thumbnail_url']}")
        st.write(f"🏷️ タグ: {row['tags']}")

        if st.button(f"🐦 ツイートする", key=f"tweet_{i}"):
            success = post_tweet(api, row["tweet_text"], row["thumbnail_url"], row["tags"])
            if success:
                df.loc[i, "posted"] = True
                df.to_csv(CSV_FILE, index=False)
                st.success(f"✅ ツイートしました: {row['title']}")
                st.experimental_rerun()

with tab2:
    st.subheader("✅ 投稿済みリスト")
    st.dataframe(df[df["posted"] == True])
