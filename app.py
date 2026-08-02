import streamlit as st
from groq import Groq
import base64

st.set_page_config(page_title="Decode by Quaarrd", page_icon="🔎", layout="centered")

# ---------- SETUP ----------
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

VISION_MODEL = "qwen/qwen3.6-27b"       # image understanding
TEXT_MODEL = "openai/gpt-oss-120b"      # reasoning / final answer

MODES = {
    "🧾 Split It": {
        "desc": "Photo of a receipt → fair bill split",
        "vision_prompt": (
            "Read this receipt carefully. Extract every line item with its exact "
            "price, and the total (including tax/tip if shown). Return it as a "
            "clean plain-text list, one item per line, then the total on its own line."
        ),
        "followup_label": "Who ordered what? (e.g. 'Alice: burger, fries. Bob: pizza, coke. Split shared items evenly')",
        "followup_prompt": (
            "Here is the receipt data:\n{vision_output}\n\n"
            "Here is how people split the items:\n{user_input}\n\n"
            "Calculate exactly how much each person owes, including their fair "
            "share of tax/tip split proportionally. Show a clear per-person "
            "breakdown and the math, then a final 'Amount Owed' summary."
        ),
    },
    "🐛 Fix It": {
        "desc": "Photo/paste of a code error → plain-English fix",
        "vision_prompt": (
            "Read this code error, stack trace, or code screenshot exactly as "
            "written. Transcribe the error message and any visible code faithfully."
        ),
        "followup_label": "Anything else about your setup? (language, what you were trying to do) — optional",
        "followup_prompt": (
            "Here is the error/code that was read from the image:\n{vision_output}\n\n"
            "Extra context from the user:\n{user_input}\n\n"
            "Explain in plain, beginner-friendly English: (1) what this error means, "
            "(2) the most likely cause, (3) a step-by-step fix. Keep it clear and "
            "encouraging, no unnecessary jargon."
        ),
    },
    "🍳 Cook It": {
        "desc": "Photo of your fridge/pantry → a recipe from what you have",
        "vision_prompt": (
            "Look at this photo of a fridge or pantry. List every food ingredient "
            "you can identify, as a clean bullet list. Be specific but don't guess "
            "wildly at things you can't see clearly."
        ),
        "followup_label": "Any preferences? (e.g. vegetarian, quick meal, spicy) — optional",
        "followup_prompt": (
            "Here are the ingredients spotted in the photo:\n{vision_output}\n\n"
            "User preferences:\n{user_input}\n\n"
            "Suggest one simple, realistic recipe using mostly these ingredients "
            "(a few common pantry staples like oil/salt are OK to assume). Give a "
            "short ingredient list and clear numbered steps."
        ),
    },
}

# ---------- HELPERS ----------
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode("utf-8")


def run_vision(image_b64, prompt):
    resp = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                ],
            }
        ],
        max_tokens=1200,
    )
    return resp.choices[0].message.content


def run_text(prompt):
    resp = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200,
    )
    return resp.choices[0].message.content


# ---------- UI ----------
st.title("🔎 Decode")
st.caption("by Quaarrd — snap a photo, pick a mode, get an instant AI answer.")

mode = st.radio(
    "What do you need help with?",
    list(MODES.keys()),
    format_func=lambda m: f"{m} — {MODES[m]['desc']}",
)

st.divider()

image_source = st.radio("Image source", ["Upload", "Camera"], horizontal=True)
uploaded_file = (
    st.file_uploader("Upload a photo", type=["jpg", "jpeg", "png"])
    if image_source == "Upload"
    else st.camera_input("Take a photo")
)

if uploaded_file:
    st.image(uploaded_file, caption="Your photo", use_container_width=True)

    if "vision_output" not in st.session_state:
        st.session_state.vision_output = None
    if "last_mode" not in st.session_state or st.session_state.last_mode != mode:
        st.session_state.vision_output = None
        st.session_state.last_mode = mode

    if st.session_state.vision_output is None:
        if st.button("🔍 Analyze photo", type="primary"):
            with st.spinner("Reading your photo..."):
                image_b64 = encode_image(uploaded_file)
                st.session_state.vision_output = run_vision(
                    image_b64, MODES[mode]["vision_prompt"]
                )
            st.rerun()

    if st.session_state.vision_output:
        with st.expander("What the AI saw", expanded=False):
            st.write(st.session_state.vision_output)

        user_input = st.text_input(MODES[mode]["followup_label"], key=f"input_{mode}")

        if st.button("✨ Get my answer", type="primary"):
            with st.spinner("Working it out..."):
                final_prompt = MODES[mode]["followup_prompt"].format(
                    vision_output=st.session_state.vision_output,
                    user_input=user_input if user_input else "(none provided)",
                )
                answer = run_text(final_prompt)
            st.success("Done!")
            st.markdown(answer)
else:
    st.info("Upload or take a photo to get started 👆")
