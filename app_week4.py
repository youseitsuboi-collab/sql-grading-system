import os
import tempfile
import streamlit as st

from utils.docx_reader import read_docx
from utils.question_splitter_week4 import split_week4_report
from week4_grader import grade_week4


# ============================================================
# ページ設定
# ============================================================

st.set_page_config(
    page_title="情報システム実験 第4週 採点システム",
    page_icon="📝",
    layout="wide"
)

st.title("情報システム実験 第4週 採点システム")

st.write(
    "第4週のレポート（Wordファイル）をアップロードすると、"
    "課題2（SQL1～SQL8）と課題4（企画クエリ）を一括で採点します。"
)


# ============================================================
# ファイルアップロード
# ============================================================

uploaded_file = st.file_uploader(
    "採点するWordファイルを選択してください",
    type=["docx"]
)


# ============================================================
# 採点
# ============================================================

if uploaded_file is not None:

    st.success(f"選択中のファイル：{uploaded_file.name}")

    if st.button("採点開始", type="primary"):

        try:
            with st.spinner("レポートを解析・採点しています..."):

                # 一時Wordファイルを作成
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".docx"
                ) as tmp:

                    tmp.write(uploaded_file.getbuffer())
                    temp_path = tmp.name

                # Word読み込み
                text = read_docx(temp_path)

                # 第4週レポート解析
                parsed_report = split_week4_report(text)

                # 課題2＋課題4を一括採点
                result = grade_week4(parsed_report)

                # 結果を保持
                st.session_state["week4_result"] = result
                st.session_state["week4_filename"] = uploaded_file.name

                # 一時ファイル削除
                os.remove(temp_path)

            st.success("採点が完了しました。")

        except Exception as e:
            st.error("採点中にエラーが発生しました。")
            st.exception(e)


# ============================================================
# 採点結果表示
# ============================================================

if "week4_result" in st.session_state:

    result = st.session_state["week4_result"]

    st.divider()

    st.header("採点結果")

    # --------------------------------------------------------
    # 総合結果
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    assignment2 = result["assignment2"]
    assignment4 = result["assignment4"]

    col1.metric(
        "課題2",
        f'{assignment2["total_score"]} / {assignment2["max_score"]} 点'
    )

    col2.metric(
        "課題4",
        f'{assignment4["total_score"]} / {assignment4["max_score"]} 点'
    )

    col3.metric(
        "合計",
        f'{result["total_score"]} / {result["max_score"]} 点'
    )

    st.divider()

    # --------------------------------------------------------
    # 課題2
    # --------------------------------------------------------

    st.header("課題2 SQL1～SQL8")

    for sql_name, sql_result in assignment2["queries"].items():

        score = sql_result.get("score", 0)
        max_score = sql_result.get("max_score", 0)

        with st.expander(
            f"{sql_name}　{score} / {max_score} 点",
            expanded=False
        ):

            for item in sql_result.get("items", []):

                grade = item.get("grade", "×")
                item_name = item.get("item", "")
                item_score = item.get("score", 0)
                answer = item.get("answer", "")
                reason = item.get("reason", "")

                if not str(answer).strip():
                    answer = "（未回答）"

                st.markdown(
                    f"### {grade} {item_name}　[{item_score}点]"
                )

                st.write(f"**回答：** {answer}")
                st.write(f"**理由：** {reason}")

    st.subheader(
        f'課題2 合計：{assignment2["total_score"]} / '
        f'{assignment2["max_score"]} 点'
    )

    st.divider()

    # --------------------------------------------------------
    # 課題4
    # --------------------------------------------------------

    st.header("課題4 企画クエリ")

    for project_name, project_result in assignment4["projects"].items():

        query_type = project_result.get("type", "")
        total = project_result.get("total_score", 0)

        title = project_name

        if query_type:
            title += f" {query_type}"

        with st.expander(
            f"{title}　{total} / 15 点",
            expanded=False
        ):

            for key, label in [
                ("validity", "妥当性"),
                ("originality", "オリジナリティ"),
                ("usefulness", "有用性"),
            ]:

                data = project_result.get(key, {})

                score = data.get("score", 0)
                reason = data.get("reason", "")

                st.markdown(f"### {label}：{score} / 5点")
                st.write(f"**理由：** {reason}")

    st.subheader(
        f'課題4 合計：{assignment4["total_score"]} / '
        f'{assignment4["max_score"]} 点'
    )

    st.divider()

    st.header(
        f'総合得点：{result["total_score"]} / '
        f'{result["max_score"]} 点'
    )


# ============================================================
# CSV・TXTダウンロード
# ============================================================

if "week4_result" in st.session_state:

    import csv
    import io

    result = st.session_state["week4_result"]
    csv_buffer = io.StringIO()
    txt_lines = []

    writer = csv.writer(csv_buffer)
    writer.writerow([
        "課題", "設問", "評価項目",
        "回答", "判定", "点数", "理由"
    ])

    txt_lines.append("情報システム実験 第4週 採点結果")
    txt_lines.append("=" * 50)

    # 課題2
    a2 = result["assignment2"]
    txt_lines.append("\n【課題2 SQL1～SQL8】")

    for sql_name, sql_result in a2["queries"].items():
        txt_lines.append(
            f'\n【{sql_name}】'
            f' {sql_result["score"]} / {sql_result["max_score"]} 点'
        )

        for item in sql_result.get("items", []):
            name = item.get("item", "")
            answer = item.get("answer", "") or "（未回答）"
            grade = item.get("grade", "×")
            score = item.get("score", 0)
            reason = item.get("reason", "")

            writer.writerow([
                "課題2", sql_name, name,
                answer, grade, score, reason
            ])

            txt_lines.append(
                f'{grade} {name} [{score}点]\n'
                f'  回答：{answer}\n'
                f'  理由：{reason}'
            )

    txt_lines.append(
        f'\n課題2 合計：{a2["total_score"]} / '
        f'{a2["max_score"]} 点'
    )

    # 課題4
    a4 = result["assignment4"]
    txt_lines.append("\n【課題4 企画クエリ】")

    for project_name, project in a4["projects"].items():
        project_type = project.get("type", "")
        txt_lines.append(
            f'\n【{project_name} {project_type}】'
            f' {project["total_score"]} / 15 点'
        )

        for key, label in [
            ("validity", "妥当性"),
            ("originality", "オリジナリティ"),
            ("usefulness", "有用性")
        ]:
            data = project.get(key, {})
            score = data.get("score", 0)
            reason = data.get("reason", "")

            writer.writerow([
                "課題4", project_name, label,
                "", "", score, reason
            ])

            txt_lines.append(
                f'{label}：{score} / 5点\n'
                f'  理由：{reason}'
            )

    txt_lines.append(
        f'\n課題4 合計：{a4["total_score"]} / '
        f'{a4["max_score"]} 点'
    )

    txt_lines.append("\n" + "=" * 50)
    txt_lines.append(
        f'総合得点：{result["total_score"]} / '
        f'{result["max_score"]} 点'
    )

    csv_data = csv_buffer.getvalue().encode("utf-8-sig")
    txt_data = "\n".join(txt_lines)

    st.divider()
    st.subheader("採点結果のダウンロード")

    col_csv, col_txt = st.columns(2)

    with col_csv:
        st.download_button(
            "CSVをダウンロード",
            data=csv_data,
            file_name="week4_grading_result.csv",
            mime="text/csv"
        )

    with col_txt:
        st.download_button(
            "TXTをダウンロード",
            data=txt_data,
            file_name="week4_grading_result.txt",
            mime="text/plain"
        )
