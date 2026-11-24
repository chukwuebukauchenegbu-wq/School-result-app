import streamlit as st
import pandas as pd

st.set_page_config(page_title="Result Calculator", page_icon="🧮", layout="wide")
st.title("🧮 School Result Calculator")
st.write("For Form Teacher Only - No Login. Save each term to your phone, open it later.")

ALL_SUBJECTS = [
    "Agricultural Science", "Basic Science", "Basic Technology", "Biology",
    "Chemistry", "Christian Religious Studies", "Civic Education", "Computer Science",
    "Economics", "English Language", "French", "Further Mathematics",
    "Geography", "Government", "Home Economics", "Literature in English",
    "Mathematics", "Physics", "Social Studies", "Yoruba / Igbo / Hausa"
]
TERMS = ["First Term", "Second Term", "Third Term"]
ROWS = 30


# ---------- Helpers ----------
def tkey(term):
    return term.replace(" ", "_")


def grade(avg):
    if avg >= 70:
        return "A"
    elif avg >= 60:
        return "B"
    elif avg >= 50:
        return "C"
    elif avg >= 40:
        return "D"
    return "F"


def table_columns(subjects):
    cols = ["Name"]
    for s in subjects:
        cols.append(f"{s} - Test /40")
        cols.append(f"{s} - Exam /60")
    return cols


def make_empty_table(subjects):
    cols = table_columns(subjects)
    return pd.DataFrame({c: [""] * ROWS if c == "Name" else [0.0] * ROWS for c in cols})


def align_table(df, subjects):
    """Fit any table to the current subjects, keeping names and scores that still match."""
    cols = table_columns(subjects)
    out = df.reindex(columns=cols)
    out["Name"] = out["Name"].fillna("").astype(str)
    for c in cols[1:]:
        out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0.0)
    return out.reset_index(drop=True)


def make_column_config(subjects):
    cfg = {"Name": st.column_config.TextColumn("Name")}
    for s in subjects:
        cfg[f"{s} - Test /40"] = st.column_config.NumberColumn(
            f"{s} - Test /40", min_value=0, max_value=40
        )
        cfg[f"{s} - Exam /60"] = st.column_config.NumberColumn(
            f"{s} - Exam /60", min_value=0, max_value=60
        )
    return cfg


def calculate_term(df_input, subjects):
    df = df_input.copy()
    df["Name"] = df["Name"].fillna("").astype(str).str.strip()
    df = df[df["Name"] != ""]
    if df.empty:
        return None

    result = pd.DataFrame({"Name": df["Name"]})
    total_cols = []
    for s in subjects:
        t = pd.to_numeric(df[f"{s} - Test /40"], errors="coerce").fillna(0)
        e = pd.to_numeric(df[f"{s} - Exam /60"], errors="coerce").fillna(0)
        result[f"{s} - Test"] = t
        result[f"{s} - Exam"] = e
        result[f"{s} - Total"] = t + e
        total_cols.append(f"{s} - Total")

    result["Overall Total"] = result[total_cols].sum(axis=1)
    result["Average"] = (result["Overall Total"] / len(subjects)).round(2)
    result["Grade"] = result["Average"].apply(grade)
    result["Position"] = result["Overall Total"].rank(ascending=False, method="min").astype(int)
    return result.sort_values("Position").reset_index(drop=True)


# ---------- Top controls ----------
st.session_state.setdefault("custom_subjects", [])
st.session_state.setdefault(
    "selected_subjects", ["Agricultural Science", "Biology", "English Language", "Mathematics"]
)


def add_custom_subject():
    name = st.session_state.get("custom_input", "").strip()
    if name:
        if name not in ALL_SUBJECTS and name not in st.session_state.custom_subjects:
            st.session_state.custom_subjects.append(name)
        if name not in st.session_state.selected_subjects:
            st.session_state.selected_subjects.append(name)
    st.session_state.custom_input = ""


col_a, col_b = st.columns(2)
with col_a:
    class_name = st.selectbox("Select Class", ["JSS 1", "JSS 2", "JSS 3", "SSS 1", "SSS 2", "SSS 3"])
with col_b:
    session_name = st.text_input("Session Name e.g. 2026/2027", value="2026/2027")
safe_session = session_name.replace("/", "-").strip() or "session"

selected = st.multiselect(
    "Select Subjects For This Class",
    ALL_SUBJECTS + st.session_state.custom_subjects,
    key="selected_subjects",
)

col_c, col_d = st.columns([3, 1])
with col_c:
    st.text_input("Add your own subject if not in list (Optional)", key="custom_input")
with col_d:
    st.write("")
    st.write("")
    st.button("➕ Add subject", on_click=add_custom_subject)

if not selected:
    st.warning("Select at least one subject to begin.")
    st.stop()

st.divider()

# ---------- Tabs ----------
tabs = st.tabs(["📘 FIRST TERM", "📗 SECOND TERM", "📙 THIRD TERM", "🏆 OVERALL 3 TERMS"])

for tab, term in zip(tabs[:3], TERMS):
    k = tkey(term)
    base_key = f"base_{k}"      # table given to the editor. Never overwritten while typing.
    data_key = f"data_{k}"      # latest edited copy, used for saving and subject changes
    ver_key = f"ver_{k}"        # bump this only when we deliberately replace the table
    sig_key = f"sig_{k}"        # remembers which subjects the table was built for
    seen_key = f"seen_{k}"      # remembers which uploaded file was already loaded
    res_key = f"result_{k}"

    # First run for this term
    if base_key not in st.session_state:
        st.session_state[base_key] = make_empty_table(selected)
        st.session_state[data_key] = st.session_state[base_key]
        st.session_state[ver_key] = 0
        st.session_state[sig_key] = tuple(selected)

    # Subjects changed: rebuild the table but keep names and matching scores
    if st.session_state[sig_key] != tuple(selected):
        st.session_state[base_key] = align_table(st.session_state[data_key], selected)
        st.session_state[data_key] = st.session_state[base_key]
        st.session_state[sig_key] = tuple(selected)
        st.session_state[ver_key] += 1

    with tab:
        st.subheader(f"{term} - {class_name} - {session_name}")
        st.info("Type names and scores. Test /40, Exam /60. Click Calculate when done.")

        # Open a saved scores sheet
        uploaded = st.file_uploader(
            f"Open Saved {term} Scores Sheet (if you saved before) - Optional",
            type=["csv"],
            key=f"up_{k}",
        )
        if uploaded is not None:
            file_id = f"{uploaded.name}-{uploaded.size}"
            if st.session_state.get(seen_key) != file_id:  # load each file only once
                try:
                    loaded = pd.read_csv(uploaded)
                    score_cols = table_columns(selected)[1:]
                    missing = [c for c in score_cols if c not in loaded.columns]
                    if "Name" not in loaded.columns or len(missing) == len(score_cols):
                        st.error(
                            "This file does not match the selected subjects. "
                            "Open the 'Scores Sheet' file (not the Result file), "
                            "and make sure the same subjects are selected."
                        )
                    else:
                        st.session_state[base_key] = align_table(loaded, selected)
                        st.session_state[data_key] = st.session_state[base_key]
                        st.session_state[ver_key] += 1
                        st.session_state[seen_key] = file_id
                        st.success(f"Opened saved file with {len(loaded)} rows.")
                        if missing:
                            st.warning("Some subjects were not found in the file, so they start at 0.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Could not open file: {e}")

        # The editor: its input stays fixed, so typing is never wiped
        edited = st.data_editor(
            st.session_state[base_key],
            num_rows="dynamic",
            use_container_width=True,
            column_config=make_column_config(selected),
            key=f"editor_{k}_{st.session_state[ver_key]}",
        )
        st.session_state[data_key] = edited

        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"✅ Calculate {term} Result", key=f"calc_{k}", type="primary"):
                res = calculate_term(edited, selected)
                if res is None:
                    st.error("Type at least one student name.")
                else:
                    st.session_state[res_key] = res
                    names = res["Name"].str.lower()
                    if names.duplicated().any():
                        dups = res.loc[names.duplicated(keep=False), "Name"].unique().tolist()
                        st.warning(f"Repeated names found: {', '.join(dups)}. Please check.")
        with c2:
            st.download_button(
                f"💾 Save {term} Scores Sheet (to continue later)",
                edited.to_csv(index=False),
                f"{class_name}_{term}_{safe_session}_Scores.csv",
                "text/csv",
                key=f"save_scores_{k}",
            )

        st.caption("If you change any score after calculating, click Calculate again.")

        if res_key in st.session_state:
            res = st.session_state[res_key]
            st.subheader(f"📋 {term} Final Result")
            st.dataframe(res, use_container_width=True)
            st.download_button(
                f"💾 Save {term} Result To My Phone",
                res.to_csv(index=False),
                f"{class_name}_{term}_{safe_session}_Result.csv",
                "text/csv",
                key=f"save_result_{k}",
            )

# ---------- Overall ----------
with tabs[3]:
    st.subheader(f"🏆 Overall - 3 Terms Combined - {class_name} - {session_name}")
    st.write("Combines First, Second and Third Term into one overall position.")
    st.info("Calculate First, Second and Third Term in their tabs first, then click below.")

    if st.button("✅ Calculate Overall 3 Terms Result", type="primary"):
        results = [st.session_state.get(f"result_{tkey(t)}") for t in TERMS]
        if any(r is None for r in results):
            st.error("Calculate First Term, Second Term AND Third Term first.")
        else:
            parts = []
            for t, r in zip(TERMS, results):
                p = r[["Name", "Overall Total"]].copy()
                p["key"] = p["Name"].str.lower().str.strip()
                p = p.drop_duplicates("key").rename(columns={"Overall Total": f"{t} Total"})
                parts.append(p)

            m = pd.concat([p[["key", "Name"]] for p in parts]).drop_duplicates("key")
            total_cols = [f"{t} Total" for t in TERMS]
            for t, p in zip(TERMS, parts):
                m = m.merge(p[["key", f"{t} Total"]], on="key", how="left")

            incomplete = m[m[total_cols].isna().any(axis=1)]["Name"].tolist()
            m[total_cols] = m[total_cols].fillna(0)
            m["Overall Total (3 Terms)"] = m[total_cols].sum(axis=1)
            m["Overall Average"] = (m["Overall Total (3 Terms)"] / (3 * len(selected))).round(2)
            m["Grade"] = m["Overall Average"].apply(grade)
            m["Overall Position"] = m["Overall Total (3 Terms)"].rank(ascending=False, method="min").astype(int)
            m = m.drop(columns="key").sort_values("Overall Position").reset_index(drop=True)

            st.session_state["result_overall"] = m
            st.session_state["overall_incomplete"] = incomplete
            st.balloons()

    if "result_overall" in st.session_state:
        m = st.session_state["result_overall"]
        incomplete = st.session_state.get("overall_incomplete", [])
        if incomplete:
            st.warning(
                "These students are not in all 3 terms, so the missing term counts as 0: "
                + ", ".join(incomplete)
            )
        st.dataframe(m, use_container_width=True)
        st.success(f"Overall done! {len(m)} students")
        st.download_button(
            "💾 Save Overall Result To My Phone",
            m.to_csv(index=False),
            f"{class_name}_Overall_3_Terms_{safe_session}.csv",
            "text/csv",
        )
