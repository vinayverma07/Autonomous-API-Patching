"""
Module: Streamlit Front-End Interface
File Path: src/patching_agent/dashboard.py
Description: Renders an engineering control workspace that communicates 
             with the FastAPI backend service asynchronously.
"""

import time
import uuid
import requests
import streamlit as st

st.set_page_config(
    page_title="Self-Healing API Patching Agent",
    page_icon="🤖",
    layout="wide"
)

API_BASE_URL = "http://127.0.0.1:8000"

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "active_job_id" not in st.session_state:
    st.session_state.active_job_id = None

st.title("🤖 Self-Healing API Patching Agent")
st.markdown(
    "An autonomous Agentic RAG system that detects API runtime failures, "
    "retrieves documentation, and deploys verified code patches."
)
st.divider()

with st.sidebar:
    st.header("⚙️ Core Controls")
    st.info(f"**Session Identifier:**\n`{st.session_state.session_id}`")
    
    # --- CORRECTED: Ping /api/health instead of /docs ---
    try:
        api_check = requests.get(f"{API_BASE_URL}/api/health", timeout=2)
        if api_check.status_code == 200 and api_check.json().get("status") == "online":
            st.success("FastAPI Backend: **Connected**")
        else:
            st.warning("FastAPI Backend: **Unreachable**")
    except Exception:
        st.error("FastAPI Backend: **Offline** (Run `uvicorn patching_agent.main:app` first)")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📥 Inbound Failure Diagnostics")
    target_file = st.text_input("Target Broken File Path", value="src/sample_api.py")
    raw_error_logs = st.text_area("Raw API Exception Logs / Traceback Dump", height=150)
    original_code_context = st.text_area("Original Broken Code Base Content", height=200)

    if st.button("🚀 Execute Autonomous Repair Loop", type="primary", use_container_width=True):
        if not raw_error_logs.strip() or not original_code_context.strip():
            st.error("Please populate both error logs and code contents to begin.")
        else:
            payload = {
                "target_file_path": target_file,
                "raw_logs": raw_error_logs,
                "original_code": original_code_context
            }
            try:
                res = requests.post(f"{API_BASE_URL}/api/repair", json=payload)
                if res.status_code == 202:
                    job_data = res.json()
                    st.session_state.active_job_id = job_data["session_id"]
                    st.success(f"Repair Job Queued! Token: `{job_data['session_id']}`")
                else:
                    st.error(f"Failed to submit job: {res.text}")
            except Exception as e:
                st.error(f"Could not connect to FastAPI server: {e}")

with col_right:
    st.subheader("🧠 Agentic Lifecycle Orchestration")
    
    if not st.session_state.active_job_id:
        st.info("System Idle. Submit a repair request to initialize the repair pipeline.")
    else:
        status_placeholder = st.empty()
        patch_placeholder = st.empty()
        
        while True:
            try:
                status_res = requests.get(f"{API_BASE_URL}/api/status/{st.session_state.active_job_id}")
                if status_res.status_code == 200:
                    job = status_res.json()
                    current_status = job.get("status", "unknown")
                    
                    with status_placeholder.container():
                        st.markdown(f"**Current Execution Status:** `{current_status}`")
                        
                    if current_status in ["patch_validated_successfully", "successfully_patched"]:
                        st.success("🎉 Code Repair Successful! Patch Applied & Validated.")
                        if job.get("generated_patch"):
                            patch_placeholder.code(job["generated_patch"], language="python")
                        break
                    elif current_status in ["failed_to_patch", "execution_error", "unit_tests_failed"]:
                        st.error(f"❌ Repair Process Failed with status: `{current_status}`")
                        if job.get("generated_patch"):
                            st.subheader("Failed Patch Proposal:")
                            st.code(job["generated_patch"], language="python")
                        if job.get("error"):
                            st.caption(f"Error Details: {job['error']}")
                        break
                    
                    time.sleep(1.5)
                else:
                    st.error("Failed to fetch job status metrics.")
                    break
            except Exception as err:
                st.error(f"Error polling repair status: {err}")
                break





# """
# Module: Streamlit Front-End Interface
# File Path: src/patching_agent/dashboard.py
# Description: Renders an engineering control workspace that communicates 
#              with the FastAPI backend service asynchronously.
# """

# import uuid
# import streamlit as st

# st.set_page_config(
#     page_title="Self-Healing API Patching Agent",
#     page_icon="🤖",
#     layout="wide"
# )

# if "session_id" not in st.session_state:
#     st.session_state.session_id = str(uuid.uuid4())
# if "agent_running" not in st.session_state:
#     st.session_state.agent_running = False

# st.title("🤖 Self-Healing API Patching Agent")
# st.markdown(
#     "An autonomous Agentic RAG system that detects API runtime failures, "
#     "retrieves documentation, and deploys verified code patches."
# )
# st.divider()

# with st.sidebar:
#     st.header("⚙️ Core Controls")
#     st.info(f"**Active Session:**\n`{st.session_state.session_id}`")
#     st.success("Ollama Engine: **Connected**")
#     st.success("MongoDB Atlas: **Connected**")

# col_left, col_right = st.columns([1, 1])

# with col_left:
#     st.subheader("📥 Inbound Failure Diagnostics")
#     target_file = st.text_input("Target Broken File Path", value="src/sample_api.py")
#     raw_error_logs = st.text_area("Raw API Exception Logs / Traceback Dump", height=150)
#     original_code_context = st.text_area("Original Broken Code Base Content", height=200)

#     if st.button("🚀 Execute Autonomous Repair Loop", type="primary", use_container_width=True):
#         if not raw_error_logs.strip() or not original_code_context.strip():
#             st.error("Please populate both error logs and code contents to begin.")
#         else:
#             st.session_state.agent_running = True

# with col_right:
#     st.subheader("🧠 Agentic Lifecycle Orchestration")
#     if not st.session_state.agent_running:
#         st.info("System Idle. Awaiting inputs to initialize the repair pipeline.")
#     else:
#         with st.status("Agent actively diagnosing environment...", expanded=True) as status:
#             st.write("🏃 Initializing Failure Detection Agent...")
#             st.write("🔍 Parsing crash logs to optimize RAG search string...")
#             st.write("📚 Fetching reference coordinates from MongoDB Atlas...")
#             status.update(label="Repair sequence processed!", state="complete", expanded=True)
#         st.success("🎉 Code Repair Successful! Patch Applied Safely.")