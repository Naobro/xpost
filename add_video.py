import streamlit as st
import pandas as pd
import os
import re
import requests
from requests.auth import HTTPBasicAuth
import tempfile
from config import WP_USER, WP_APP_PASSWORD, WP_API_URL, CSV_FILE

st.title("📹 アフィリエイト広告登録 & WordPress投稿（サムネ自動取得）")

# ✅ WordPressカテゴリ一覧取得
def get_wp_categories():
    url = f"{WP_API_URL}/categories?per_page=100"
    try:
        res = requests.get(url, auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD))
        if res.status_code == 200:
            return {cat["name"]: cat["id"] for cat in res.json()}
    except:
        pass
    return {"未分類": 1}

categories = get_wp_categories()

# ✅ CSV読み込み
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=["title", "category", "tweet_text", "script", "thumbnail_url"])

# ✅ WordPress メディアアップロード関数
def upload_media_to_wp(file_path, file_name, mime_type):
    url = f"{WP_API_URL}/media"
    headers = {
        "Content-Disposition": f'attachment; filename="{file_name}"',
        "Content-Type": mime_type
    }
    auth = HTTPBasicAuth(WP_USER, WP_APP_PASSWORD)

    with open(file_path, "rb") as f:
        res = requests.post(url, headers=headers, auth=auth, files={"file": f})

    if res.status_code in [200, 201]:
        return res.json().get("id"), res.json().get("source_url")
    else:
        st.error(f"メディアアップロード失敗: {res.status_code} {res.text}")
        return None, None

# ✅ WordPress 投稿作成関数
def create_wp_post(title, content, category_id, featured_image_id=None):
    url = f"{WP_API_URL}/posts"
    auth = HTTPBasicAuth(WP_USER, WP_APP_PASSWORD)

    post_data = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": [category_id],
    }
    if featured_image_id:
        post_data["featured_media"] = featured_image_id

    res = requests.post(url, auth=auth, json=post_data)

    if res.status_code in [200, 201]:
        return True
    else:
        st.error(f"記事投稿失敗: {res.status_code} {res.text}")
        return False

# ✅ scriptタグからサムネイルURL抽出
def extract_thumbnail_url(script_text):
    match = re.search(r"img=(https?://[^\s&]+)", script_text)
    return match.group(1) if match else None

# ✅ 入力フォーム
st.subheader("🎥 新しい広告を追加")
title = st.text_input("タイトル (title)")
category_name = st.selectbox("カテゴリ (category)", options=list(categories.keys()))
tweet_text = st.text_area("ツイート本文 (tweet_text)")
script = st.text_area("広告スクリプトタグ (script)")

# ✅ ボタン押下時
if st.button("✅ 投稿する（サムネ自動取得）"):
    if title and tweet_text and script:
        if title in df["title"].values:
            st.warning("⚠️ このタイトルは既に登録済みです。スキップします。")
        else:
            thumb_url = extract_thumbnail_url(script)
            thumb_id, uploaded_thumb_url = None, None

            if thumb_url:
                try:
                    res = requests.get(thumb_url, stream=True)
                    if res.status_code == 200:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_img:
                            tmp_img.write(res.content)
                            tmp_img_path = tmp_img.name
                        thumb_id, uploaded_thumb_url = upload_media_to_wp(tmp_img_path, "thumbnail.jpg", "image/jpeg")
                except Exception as e:
                    st.error(f"サムネイル取得失敗: {e}")

            content = f"<p>{tweet_text}</p>\n\n{script}"
            category_id = categories.get(category_name, 1)

            if create_wp_post(title, content, category_id, featured_image_id=thumb_id):
                st.success("✅ WordPressに投稿しました！")

                new_row = pd.DataFrame(
                    [[title, category_name, tweet_text, script, uploaded_thumb_url or ""]],
                    columns=["title", "category", "tweet_text", "script", "thumbnail_url"]
                )
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(CSV_FILE, index=False)
                st.success("✅ CSVに追加しました！")
    else:
        st.error("❌ すべての項目を入力してください")

st.subheader("📄 登録済み広告リスト")
st.dataframe(df)