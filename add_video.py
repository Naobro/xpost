import streamlit as st
import pandas as pd
import os
import requests
import re
import tempfile
from requests.auth import HTTPBasicAuth
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

# ✅ 画像URLからダウンロードしてWPにアップロード
def upload_image_from_url(image_url):
    try:
        img_data = requests.get(image_url, timeout=10).content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_img:
            tmp_img.write(img_data)
            tmp_img_path = tmp_img.name

        url = f"{WP_API_URL}/media"
        headers = {
            "Content-Disposition": 'attachment; filename="thumbnail.jpg"',
            "Content-Type": "image/jpeg"
        }
        auth = HTTPBasicAuth(WP_USER, WP_APP_PASSWORD)

        with open(tmp_img_path, "rb") as f:
            res = requests.post(url, headers=headers, auth=auth, files={"file": f})

        if res.status_code in [200, 201]:
            return res.json().get("id"), res.json().get("source_url")
        else:
            st.error(f"メディアアップロード失敗: {res.status_code} {res.text}")
            return None, None
    except Exception as e:
        st.error(f"画像取得エラー: {e}")
        return None, None

# ✅ WordPress 投稿作成
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

# ✅ スクリプトから img= のURLを取得
def extract_img_url(script_text):
    match = re.search(r'img=(https?://[^\s"&]+)', script_text)
    if match:
        return match.group(1)
    return None

# ✅ 入力フォーム
st.subheader("🎥 新しい広告を追加")
title = st.text_input("タイトル (title)")
category_name = st.selectbox("カテゴリ (category)", options=list(categories.keys()))
tweet_text = st.text_area("ツイート本文 (tweet_text)")
script = st.text_area("広告スクリプトタグ (script)")

# ✅ ボタン押下時
if st.button("✅ 投稿する（動画なし）"):
    if title and tweet_text and script:
        with st.spinner("📤 サムネイル取得中..."):
            img_url = extract_img_url(script)

            if img_url:
                thumb_id, thumb_url = upload_image_from_url(img_url)
            else:
                thumb_id, thumb_url = None, None
                st.warning("⚠️ スクリプト内に img= が見つかりませんでした。")

            category_id = categories.get(category_name, 1)
            content = f"{script}\n\n<p>サンプル動画👇</p>"

            if create_wp_post(title, content, category_id, featured_image_id=thumb_id):
                st.success("✅ WordPressに投稿しました！")

                new_row = pd.DataFrame(
                    [[title, category_name, tweet_text, script, thumb_url if thumb_url else ""]],
                    columns=["title", "category", "tweet_text", "script", "thumbnail_url"]
                )
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(CSV_FILE, index=False)
                st.success("✅ CSVに追加しました！")
            else:
                st.error("❌ WordPress記事投稿に失敗しました")
    else:
        st.error("❌ すべての項目を入力してください")

st.subheader("📄 登録済み広告リスト")
st.dataframe(df)