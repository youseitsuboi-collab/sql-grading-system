import os
import streamlit as st
import pandas as pd

from week2_grader import (
    uploaded_docx_to_markdown,
    grade_markdown
)


# ==========================================
# 基本設定
# ==========================================

st.set_page_config(
    page_title="情報システム実験 第2週 採点システム",
    page_icon="📝",
    layout="wide"
)


# ==========================================
# OpenAI APIキー
# ==========================================
# ↓↓↓ 自分のOpenAI APIキーをここに貼る ↓↓↓

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY","")


# ==========================================
# パスワード
# ==========================================
# 現在はテスト段階なのでパスワードなし

def check_password():
    return True


if not check_password():
    st.stop()


# ==========================================
# Session State 初期化
# ==========================================

if "grading_results" not in st.session_state:
    st.session_state.grading_results = None

if "grading_total" not in st.session_state:
    st.session_state.grading_total = None

if "grading_filename" not in st.session_state:
    st.session_state.grading_filename = None


# ==========================================
# 画面タイトル
# ==========================================

st.title("情報システム実験 第2週 採点システム")

st.caption("SPJクエリ")

st.info(
    "学生レポート（Word）をアップロードすると、"
    "クエリ設計を評価項目ごとに自動採点します。"
)


# ==========================================
# Wordファイルアップロード
# ==========================================

uploaded = st.file_uploader(
    "学生レポート（.docx）を選択してください",
    type=["docx"]
)


# ==========================================
# ファイルがアップロードされた場合
# ==========================================

if uploaded is not None:

    st.write(
        f"選択中のファイル：{uploaded.name}"
    )

    # 別のファイルを選択した場合は前回結果を消す
    if (
        st.session_state.grading_filename is not None
        and st.session_state.grading_filename != uploaded.name
    ):
        st.session_state.grading_results = None
        st.session_state.grading_total = None
        st.session_state.grading_filename = None


    # ======================================
    # 採点ボタン
    # ======================================

    if st.button(
        "採点を実行",
        type="primary"
    ):

        # APIキー確認
        if (
            not OPENAI_API_KEY
            or OPENAI_API_KEY
            == "ここに自分のOpenAI APIキーを貼る"
        ):

            st.error(
                "app.py にOpenAI APIキーを設定してください。"
            )

            st.stop()


        try:

            # ==================================
            # Word → Markdown
            # ==================================

            with st.spinner(
                "Wordファイルを解析しています..."
            ):

                student_md = (
                    uploaded_docx_to_markdown(
                        uploaded.getvalue()
                    )
                )


            # ==================================
            # 模範解答読み込み
            # ==================================

            with open(
                "data/new_spj_markdown/model_answer.md",
                "r",
                encoding="utf-8"
            ) as f:

                model_md = f.read()



            # ==================================
            # GPT採点
            # ==================================

            with st.spinner(
                "GPTで採点しています..."
            ):

                results, total = grade_markdown(
                    student_md,
                    model_md,
                    OPENAI_API_KEY
                )


            # ==================================
            # 採点結果を保存
            # ==================================

            st.session_state.grading_results = results
            st.session_state.grading_total = total
            st.session_state.grading_filename = uploaded.name


        # ======================================
        # エラー処理
        # ======================================

        except Exception as e:

            st.error(
                "採点中にエラーが発生しました。"
            )

            st.exception(e)


# ==========================================
# 保存されている採点結果を表示
# ==========================================

if (
    st.session_state.grading_results is not None
    and st.session_state.grading_total is not None
):

    results = st.session_state.grading_results
    total = st.session_state.grading_total
    filename = st.session_state.grading_filename


    # ======================================
    # 採点完了
    # ======================================

    st.success(
        "採点が完了しました。"
    )


    # ======================================
    # 総合点
    # ======================================

    st.metric(
        "総合計点",
        f"{total} / 40"
    )


    # ======================================
    # 各設問の結果
    # ======================================

    rows = []
    full_text = []


    for r in results:

        rows.append(
            {
                "設問": f"Q{r['q_num']}",
                "得点": r["score"],
                "満点": 5
            }
        )


        full_text.append(
            "=" * 40
        )

        full_text.append(
            f"Q{r['q_num']}"
        )

        full_text.append(
            r["text"]
        )


        # ==================================
        # ブラウザ上に詳細結果表示
        # ==================================

        with st.expander(
            f"Q{r['q_num']}　"
            f"{r['score']} / 5",
            expanded=True
        ):

            st.text(
                r["text"]
            )


    # ======================================
    # 得点一覧
    # ======================================

    st.subheader(
        "得点一覧"
    )


    df = pd.DataFrame(
        rows
    )


    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


    # ======================================
    # CSV作成
    # ======================================

    csv_bytes = (
        df
        .to_csv(
            index=False
        )
        .encode(
            "utf-8-sig"
        )
    )


    # ======================================
    # CSVダウンロード
    # ======================================

    st.download_button(
        "得点一覧CSVをダウンロード",
        data=csv_bytes,
        file_name=(
            f"{filename.rsplit('.', 1)[0]}"
            "_scores.csv"
        ),
        mime="text/csv"
    )


    # ======================================
    # 詳細結果TXT
    # ======================================

    txt = (
        "\n".join(full_text)
        + "\n"
        + "=" * 40
        + "\n"
        + f"総合計点：{total} / 40\n"
    )


    # ======================================
    # TXTダウンロード
    # ======================================

    st.download_button(
        "詳細結果TXTをダウンロード",
        data=txt.encode(
            "utf-8"
        ),
        file_name=(
            f"{filename.rsplit('.', 1)[0]}"
            "_result.txt"
        ),
        mime="text/plain"
    )
