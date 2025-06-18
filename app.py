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
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

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

# Get responses and shuffle ONCE per question
q_responses = responses[responses['Qid'] == qid].copy()
shuffle_key = f"shuffled_{qid}"
if shuffle_key not in st.session_state:
    st.session_state[shuffle_key] = q_responses.sample(frac=1).reset_index(drop=True)
q_responses = st.session_state[shuffle_key]

# Display and rate responses
ratings = []
st.markdown("---")
for idx, row in q_responses.iterrows():
    rid = row['Rid']  # Unique ID for response, used in widget keys

    with st.container():
        st.markdown(f"**Response {idx + 1}:** {row['Response']}")
        acc = st.slider("Accuracy", 1, 5, key=f"acc_{qid}_{rid}")
        rel = st.slider("Relevance", 1, 5, key=f"rel_{qid}_{rid}")
        qual = st.slider("Quality", 1, 5, key=f"qual_{qid}_{rid}")

        ratings.append({
            "evaluator": st.session_state.evaluator,
            "qid": qid,
            "question": question,
            "ga": ga,
            "rid": rid,
            "response": row['Response'],
            "accuracy": acc,
            "relevance": rel,
            "quality": qual,
            "timestamp": datetime.now().isoformat()
        })
    st.markdown("---")

# Submission logic
if not st.session_state.submitted:
    if st.button("Submit Evaluations"):
        result_df = pd.DataFrame(ratings)
        os.makedirs("results", exist_ok=True)
        output_file = "results/responses.csv"
        result_df.to_csv(output_file, mode="a", index=False, header=not os.path.exists(output_file))
        st.session_state.submitted = True
        st.success("✅ Your ratings have been submitted.")
        st.stop()
else:
    st.success("✅ Your ratings have been submitted.")
    if st.button("Next Question"):
        st.session_state.qid_index += 1
        st.session_state.submitted = False

        # Clear slider state for next question
        keys_to_clear = [key for key in st.session_state if key.startswith(("acc_", "rel_", "qual_"))]
        for key in keys_to_clear:
            del st.session_state[key]

        # Clear shuffle cache for previous question
        st.session_state.pop(shuffle_key, None)

        st.rerun()
