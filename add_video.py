import streamlit as st
import pandas as pd
import os
import requests
from requests.auth import HTTPBasicAuth
import tempfile
from config import WP_USER, WP_APP_PASSWORD, WP_API_URL, CSV_FILE

st.title("📹 アフィリエイト広告登録 & WordPress投稿（タグ付き・動画なし）")

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
    df = pd.DataFrame(columns=["title", "category", "tweet_text", "script", "thumbnail_url", "tags", "posted"])

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
    return res.status_code in [200, 201]

# ✅ サムネイル画像アップロード
def upload_thumbnail(image_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_img:
        tmp_img.write(image_file.read())
        tmp_img_path = tmp_img.name
    return upload_media_to_wp(tmp_img_path, image_file.name, "image/jpeg")

# ==============================
# 🔹 タグリスト
# ==============================
DEFAULT_TAGS = [
    "#無修正", "#ハメ撮り", "#露出", "#人妻", "#美熟女",
    "#セフレ募集", "#中出し", "#素人動画", "#オナニー",
    "#性欲強い", "#アダルト動画", "#裏アカ女子", "#性癖晒し",
    "#AV女優", "#無料サンプル"
]

# ✅ 入力フォーム
st.subheader("🎥 新しい広告を追加")
title = st.text_input("タイトル (title)")
category_name = st.selectbox("カテゴリ (category)", options=list(categories.keys()))
tweet_text = st.text_area("ツイート本文 (tweet_text)")
script = st.text_area("広告スクリプトタグ (script)")
thumbnail_file = st.file_uploader("サムネイル画像 (jpg/png)", type=["jpg", "jpeg", "png"])

# 🔹 タグ選択（3つまで）
selected_tags = st.multiselect("タグを選択（最大3つ）", DEFAULT_TAGS, max_selections=3)
manual_tags = st.text_input("手動タグを追加（例: #東京 #アラフォー）")

# ✅ ボタン押下時
if st.button("✅ 投稿する（動画なし）"):
    if title and tweet_text and script and thumbnail_file:
        with st.spinner("📤 サムネイルをアップロード中..."):
            thumb_id, thumb_url = upload_thumbnail(thumbnail_file)

            if thumb_id:
                # 🔹 ツイート用タグ
                all_tags = " ".join(selected_tags) + (" " + manual_tags if manual_tags else "")

                # 🔹 記事本文は tweet_text + script
                content = f"<p>{tweet_text}</p>\n\n{script}"

                category_id = categories.get(category_name, 1)

                if create_wp_post(title, content, category_id, featured_image_id=thumb_id):
                    st.success("✅ WordPressに投稿しました！")

                    new_row = pd.DataFrame(
                        [[title, category_name, tweet_text, script, thumb_url, all_tags, False]],
                        columns=["title", "category", "tweet_text", "script", "thumbnail_url", "tags", "posted"]
                    )
                    df = pd.concat([df, new_row], ignore_index=True)
                    df.to_csv(CSV_FILE, index=False)
                    st.success("✅ CSVに追加しました！")
                else:
                    st.error("❌ WordPress記事投稿に失敗しました")
            else:
                st.error("❌ サムネイルアップロード失敗")
    else:
        st.error("❌ すべての項目を入力してください")

st.subheader("📄 登録済み広告リスト")
st.dataframe(df)