import streamlit as st
import pandas as pd
from datetime import datetime
from pyairtable import Table

# Airtable secrets from .streamlit/secrets.toml
AIRTABLE_API_KEY = st.secrets["airtable"]["api_key"]
AIRTABLE_BASE_ID = st.secrets["airtable"]["base_id"]
AIRTABLE_TABLE_NAME = st.secrets["airtable"]["table_name"]

table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

def get_last_completed_qid(evaluator_name):
    records = table.all(formula=f"{{evaluator}} = '{evaluator_name}'")
    if not records:
        return 0  # no previous evaluations
    completed_qids = {int(rec['fields'].get('qid', 0)) for rec in records}
    return max(completed_qids, default=0)

def upload_to_airtable(data):
    for entry in data:
        clean_entry = {}
        for k, v in entry.items():
            if k == "timestamp" and isinstance(v, (datetime, pd.Timestamp)):
                clean_entry[k] = v.date().isoformat()
            elif isinstance(v, (pd.Timestamp, datetime)):
                clean_entry[k] = v.isoformat()
            elif isinstance(v, (int, float, str, bool)):
                clean_entry[k] = v
            elif hasattr(v, 'item'):
                clean_entry[k] = v.item()
            else:
                clean_entry[k] = str(v)
        table.create(clean_entry)

# Load CSV data
questions = pd.read_csv('data/questions.csv')
responses = pd.read_csv('data/responses.csv')

# Streamlit setup
st.set_page_config(page_title="Model Evaluation", layout="wide")

# Session setup
if 'evaluator' not in st.session_state:
    st.session_state.evaluator = ""
if 'qid_index' not in st.session_state:
    st.session_state.qid_index = 0
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# Show Thank You if submitted
if st.session_state.submitted:
    st.title("🎉 Thank You!")
    st.success("Your evaluations have been successfully recorded.")
    st.stop()

# Evaluator input
if not st.session_state.evaluator:
    st.title("Welcome to the Evaluation Form")
    evaluator_name = st.text_input("Enter your name:")
    if st.button("Start Evaluation") and evaluator_name:
        st.session_state.evaluator = evaluator_name
        last_qid = get_last_completed_qid(evaluator_name)
        st.session_state.qid_index = last_qid  # resume from next qid
        st.rerun()
    st.stop()

# End condition check
if st.session_state.qid_index >= len(questions):
    st.session_state.submitted = True
    st.rerun()

# Show current question
qid_idx = st.session_state.qid_index
qrow = questions.iloc[qid_idx]
qid = qrow['Qid']
question = qrow['Question']
ga = qrow['GA']

st.subheader(f"Q{qid}: {question}")
st.markdown(f"**Gold Answer:** _{ga}_")

# Get responses
#q_responses = responses[responses['Qid'] == qid].copy()
#q_responses = q_responses.sample(frac=1).reset_index(drop=True)
if f"shuffled_responses_{qid}" not in st.session_state:
    q_responses = responses[responses['Qid'] == qid].copy()
    q_responses = q_responses.sample(frac=1).reset_index(drop=True)
    st.session_state[f"shuffled_responses_{qid}"] = q_responses
else:
    q_responses = st.session_state[f"shuffled_responses_{qid}"]

# Display in 2x2 grid
ratings = []
for i in range(0, len(q_responses), 2):
    cols = st.columns(2)
    for j in range(2):
        if i + j >= len(q_responses):
            break
        row = q_responses.iloc[i + j]
        with cols[j]:
            st.markdown(f"### Response {i + j + 1}")
            st.markdown(row['Response'])

            acc = st.selectbox(f"Accuracy (Response {i + j + 1})", list(range(1, 6)), key=f"acc_{i + j}")
            rel = st.selectbox(f"Relevance (Response {i + j + 1})", list(range(1, 6)), key=f"rel_{i + j}")
            qual = st.selectbox(f"Quality (Response {i + j + 1})", list(range(1, 6)), key=f"qual_{i + j}")

            ratings.append({
                "evaluator": st.session_state.evaluator,
                "qid": qid,
                "question": question,
                "ga": ga,
                "rid": row['Rid'],
                "response": row['Response'],
                "accuracy": acc,
                "relevance": rel,
                "quality": qual,
                "timestamp": datetime.now()
            })

# Submit button
if st.button("Submit Evaluations"):
    upload_to_airtable(ratings)
    st.session_state.qid_index += 1
    if st.session_state.qid_index >= len(questions):
        st.session_state.submitted = True
    st.rerun()