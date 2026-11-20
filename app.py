import streamlit as st
import pandas as pd

st.set_page_config(page_title="School Result App", page_icon="🏫")

USERS = {
    "admin": "admin123",
    "biology_jss2": "bio123",
    "english_jss2": "eng123",
    "maths_jss2": "maths123",
}

st.title("🏫 School Result App")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("Teacher Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if user in USERS and USERS[user] == pwd:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Wrong username or password")
    st.stop()

st.success(f"Welcome, {st.session_state.user}")
if st.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

class_name = st.selectbox("Select Class", ["JSS 1", "JSS 2", "JSS 3", "SSS 1", "SSS 2", "SSS 3"])
subject = st.text_input("Your Subject e.g. Biology")

st.subheader("Step 1: Student List (Form Teacher Only)")
student_file = st.file_uploader("Upload Student List - CSV with Name column", type=["csv", "xlsx"], key="students")
if student_file:
    if student_file.name.endswith(".csv"):
        students_df = pd.read_csv(student_file)
    else:
        students_df = pd.read_excel(student_file)
    st.session_state[f"students_{class_name}"] = students_df
    st.write(f"Loaded {len(students_df)} students for {class_name}")

st.subheader("Step 2: Upload Your Subject - Test /40 + Exam /60")
st.info("File must have: Name, Test, Exam. Test max 40, Exam max 60.")
subject_file = st.file_uploader("Upload Test + Exam for your subject", type=["csv", "xlsx"], key="subject")

if subject_file and subject:
    if subject_file.name.endswith(".csv"):
        sub_df = pd.read_csv(subject_file)
    else:
        sub_df = pd.read_excel(subject_file)
    if sub_df["Test"].max() > 40:
        st.error("Error: Test is over 40. Please check.")
    elif sub_df["Exam"].max() > 60:
        st.error("Error: Exam is over 60. Please check.")
    else:
        sub_df["Total"] = sub_df["Test"] + sub_df["Exam"]
        key = f"subjects_{class_name}"
        if key not in st.session_state:
            st.session_state[key] = {}
        st.session_state[key][subject] = sub_df[["Name", "Total"]].rename(columns={"Total": subject})
        st.success(f"Saved {subject}. Subjects so far: {list(st.session_state[key].keys())}")

st.subheader("Step 3: Final Result")
if st.button("Generate Final Broadsheet"):
    students = st.session_state.get(f"students_{class_name}")
    subjects_dict = st.session_state.get(f"subjects_{class_name}", {})
    if students is None:
        st.error("Upload student list first")
    elif len(subjects_dict) == 0:
        st.error("No subjects uploaded yet")
    else:
        merged = students.copy()
        for subj_name, df in subjects_dict.items():
            merged = merged.merge(df, on="Name", how="left")
        subject_cols = list(subjects_dict.keys())
        merged["Overall Total"] = merged[subject_cols].sum(axis=1)
        merged["Average"] = (merged["Overall Total"] / len(subject_cols)).round(2)
        def grade(a):
            if a >= 70: return "A"
            elif a >= 60: return "B"
            elif a >= 50: return "C"
            elif a >= 40: return "D"
            else: return "F"
        merged["Grade"] = merged["Average"].apply(grade)
        merged["Position"] = merged["Overall Total"].rank(ascending=False, method="min").astype(int)
        final = merged.sort_values("Position")
        st.dataframe(final)
        st.download_button("Download Printable Result", final.to_csv(index=False), f"{class_name}_final_result.csv")
        st.success(f"Done! {len(subject_cols)} subjects calculated. Max is 30.")
