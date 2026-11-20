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

# Top controls
col_a, col_b = st.columns(2)
with col_a:
    class_name = st.selectbox("Select Class", ["JSS 1", "JSS 2", "JSS 3", "SSS 1", "SSS 2", "SSS 3"])
with col_b:
    session_name = st.text_input("Session Name e.g. 2026/2027", value="2026/2027")

selected = st.multiselect("Select Subjects For This Class", ALL_SUBJECTS, default=["Agricultural Science", "Biology", "English Language", "Mathematics"])
custom = st.text_input("Add your own subject if not in list (Optional)")
if custom and custom not in ALL_SUBJECTS:
    st.info(f"Type it, then add '{custom}' to the list above next time. For now it will show after you refresh.")

st.divider()

# Helper to make empty table
def make_empty_table():
    cols = ["Name"]
    for s in selected:
        cols.append(f"{s} - Test /40")
        cols.append(f"{s} - Exam /60")
    return pd.DataFrame({c: [""]*30 if c=="Name" else [0]*30 for c in cols})

def calculate_term(df_input):
    df = df_input.copy()
    df = df[df["Name"].astype(str).str.strip() != ""]
    if len(df)==0:
        return None
    result = pd.DataFrame()
    result["Name"] = df["Name"]
    totals = []
    for s in selected:
        t_col = f"{s} - Test /40"
        e_col = f"{s} - Exam /60"
        df[t_col] = pd.to_numeric(df[t_col], errors="coerce").fillna(0)
        df[e_col] = pd.to_numeric(df[e_col], errors="coerce").fillna(0)
        total = df[t_col] + df[e_col]
        result[f"{s} - Test"] = df[t_col]
        result[f"{s} - Exam"] = df[e_col]
        result[f"{s} - Total"] = total
        totals.append(f"{s} - Total")
    result["Overall Total"] = result[totals].sum(axis=1)
    result["Average"] = (result["Overall Total"] / max(len(selected),1)).round(2)
    def grade(a):
        if a>=70: return "A"
        elif a>=60: return "B"
        elif a>=50: return "C"
        elif a>=40: return "D"
        else: return "F"
    result["Grade"] = result["Average"].apply(grade)
    result["Position"] = result["Overall Total"].rank(ascending=False, method="min").astype(int)
    result = result.sort_values("Position")
    return result

# Tabs for 3 Terms
tab1, tab2, tab3, tab_overall = st.tabs(["📘 FIRST TERM", "📗 SECOND TERM", "📙 THIRD TERM", "🏆 OVERALL 3 TERMS"])

for idx, (tab, term_name) in enumerate([(tab1, "First Term"), (tab2, "Second Term"), (tab3, "Third Term")]):
    with tab:
        st.subheader(f"{term_name} - {class_name} - {session_name}")
        st.info("Type names and scores. Test /40, Exam /60. Total calculates automatically.")

        key_df = f"df_{term_name.replace(' ','_')}"
        key_result = f"result_{term_name.replace(' ','_')}"

        # Open saved file
        uploaded = st.file_uploader(f"Open Saved {term_name} File (if you saved before) - Optional", type=["csv"], key=f"up_{term_name}")
        if uploaded:
            try:
                loaded = pd.read_csv(uploaded)
                st.session_state[key_df] = loaded
                st.success(f"Opened saved {term_name} file with {len(loaded)} students")
            except Exception as e:
                st.error(f"Could not open file: {e}")

        if key_df not in st.session_state or st.session_state.get(f"subj_{key_df}") != tuple(selected):
            st.session_state[key_df] = make_empty_table()
            st.session_state[f"subj_{key_df}"] = tuple(selected)

        edited = st.data_editor(st.session_state[key_df], num_rows="dynamic", use_container_width=True, key=f"editor_{term_name}_{len(selected)}")
        st.session_state[key_df] = edited

        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"✅ Calculate {term_name} Result", key=f"calc_{term_name}", type="primary"):
                res = calculate_term(edited)
                if res is None:
                    st.error("Type at least one student name")
                else:
                    st.session_state[key_result] = res
                    st.subheader(f"📋 {term_name} Final Result")
                    st.dataframe(res, use_container_width=True)
        with c2:
            # Show result if exists and allow save
            if key_result in st.session_state:
                res = st.session_state[key_result]
                st.download_button(f"💾 Save {term_name} To My Phone", res.to_csv(index=False), f"{class_name}_{term_name}_{session_name}_Result.csv", "text/csv", key=f"save_{term_name}")
                st.caption("This will download to your phone. Keep it safe. You can open it next term.")
        # Also show last result if exists
        if key_result in st.session_state and st.button(f"Show {term_name} Result Again", key=f"show_{term_name}"):
            st.dataframe(st.session_state[key_result], use_container_width=True)

with tab_overall:
    st.subheader(f"🏆 Overall - 3 Terms Combined - {class_name} - {session_name}")
    st.write("This will combine First Term + Second Term + Third Term and give one overall position.")
    st.info("Make sure you have calculated First, Second and Third Term above, or open your saved files in each tab first. Then click below.")
    if st.button("✅ Calculate Overall 3 Terms Result", type="primary"):
        r1 = st.session_state.get("result_First_Term")
        r2 = st.session_state.get("result_Second_Term")
        r3 = st.session_state.get("result_Third_Term")
        if r1 is None or r2 is None or r3 is None:
            st.error("You need to Calculate First Term, Second Term AND Third Term first. Go to each tab and click Calculate.")
        else:
            # Merge by Name, use Overall Total per term
            m = r1[["Name", "Overall Total"]].rename(columns={"Overall Total": "First Term Total"})
            m = m.merge(r2[["Name", "Overall Total"]].rename(columns={"Overall Total": "Second Term Total"}), on="Name", how="outer")
            m = m.merge(r3[["Name", "Overall Total"]].rename(columns={"Overall Total": "Third Term Total"}), on="Name", how="outer")
            m = m.fillna(0)
            m["Overall Total (3 Terms)"] = m["First Term Total"] + m["Second Term Total"] + m["Third Term Total"]
            m["Overall Average"] = (m["Overall Total (3 Terms)"] / 3).round(2)
            # Average per subject overall: divide by subjects
            m["Average Per Subject"] = (m["Overall Average"] / max(len(selected),1)).round(2)
            def grade_overall(a):
                if a>=70: return "A"
                elif a>=60: return "B"
                elif a>=50: return "C"
                elif a>=40: return "D"
                else: return "F"
            m["Grade"] = m["Average Per Subject"].apply(grade_overall)
            m["Overall Position"] = m["Overall Total (3 Terms)"].rank(ascending=False, method="min").astype(int)
            m = m.sort_values("Overall Position")
            st.dataframe(m, use_container_width=True)
            st.success(f"Overall Done! {len(m)} students")
            st.download_button("💾 Save Overall Result To My Phone", m.to_csv(index=False), f"{class_name}_Overall_3_Terms_{session_name}.csv", "text/csv")
            st.balloons()
