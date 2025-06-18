import streamlit as st
import pandas as pd
import random
from datetime import datetime
import os

# Load data
questions = pd.read_csv('data/questions.csv')
responses = pd.read_csv('data/responses.csv')

st.set_page_config(page_title="Model Evaluation", layout="wide")

# Session setup
if 'evaluator' not in st.session_state:
    st.session_state.evaluator = ""
if 'qid_index' not in st.session_state:
    st.session_state.qid_index = 0

# Evaluator input
if not st.session_state.evaluator:
    st.title("Welcome to the Evaluation Form")
    evaluator_name = st.text_input("Enter your name:")
    if st.button("Start Evaluation") and evaluator_name:
        st.session_state.evaluator = evaluator_name
        st.rerun()
    st.stop()

# End condition
if st.session_state.qid_index >= len(questions):
    st.success("✅ All evaluations submitted. Thank you!")
    st.stop()

# Show current question
qid_idx = st.session_state.qid_index
qrow = questions.iloc[qid_idx]
qid = qrow['Qid']
question = qrow['Question']
ga = qrow['GA']

st.subheader(f"Q{qid}: {question}")
st.markdown(f"**Gold Answer:** _{ga}_")

# Get and shuffle responses
q_responses = responses[responses['Qid'] == qid].copy()
q_responses = q_responses.sample(frac=1).reset_index(drop=True)

# Response blocks
ratings = []
st.markdown("---")
for idx, row in q_responses.iterrows():
    with st.container():
        st.markdown(f"**Response {idx+1}:** {row['Response']}")
        acc = st.slider(f"Accuracy (Response {idx+1})", 1, 5, key=f"acc_{idx}")
        rel = st.slider(f"Relevance (Response {idx+1})", 1, 5, key=f"rel_{idx}")
        qual = st.slider(f"Quality (Response {idx+1})", 1, 5, key=f"qual_{idx}")
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
            "timestamp": datetime.now().isoformat()
        })
    st.markdown("---")

# Submit button
if st.button("Submit Evaluations"):
    result_df = pd.DataFrame(ratings)
    os.makedirs("results", exist_ok=True)
    output_file = "results/responses.csv"
    result_df.to_csv(output_file, mode="a", index=False, header=not os.path.exists(output_file))
    st.session_state.qid_index += 1
    st.rerun()
