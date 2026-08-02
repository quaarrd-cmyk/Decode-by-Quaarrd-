import streamlit as st
from groq import Groq
from tavily import TavilyClient
import base64

st.set_page_config(page_title="Decode by Quaarrd", page_icon="🔎", layout="centered")

# ---------- SETUP ----------
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])

VISION_MODEL = "qwen/qwen3.6-27b"       # image understanding
TEXT_MODEL = "openai/gpt-oss-120b"      # reasoning / final answer


def web_search(query, max_results=3):
    """Search the web with Tavily and return a short combined text summary."""
    query = query.replace("\n", " ").strip()[:390]  # Tavily hard limit: 400 chars
    try:
        results = tavily.search(query=query, max_results=max_results)
        snippets = []
        for r in results.get("results", []):
            snippets.append(f"- {r.get('title', '')}: {r.get('content', '')[:400]}")
        return "\n".join(snippets) if snippets else "(no web results found)"
    except Exception as e:
        return f"(web search unavailable: {e})"


def build_search_query(vision_output, template):
    """Build a short, targeted search query instead of dumping the whole vision output in."""
    lines = vision_output.splitlines()
    brand_lines = [l.replace("BRAND:", "").strip() for l in lines if "BRAND:" in l]
    if brand_lines:
        key_text = " ".join(brand_lines[:2])  # use identified brand/product name(s)
    else:
        key_text = " ".join(lines[:3])  # fallback: first few lines only
    return template.format(vision_output=key_text)[:390]

MODES = {
    "🧾 Split It": {
        "desc": "Photo of a receipt → fair bill split",
        "vision_prompt": (
            "You may be given one or more photos of the same receipt/bill (e.g. "
            "multiple angles or a long receipt split across shots). Combine info "
            "across all photos. Read carefully. Extract every line item with its "
            "exact price, and the total (including tax/tip if shown). Return it as "
            "a clean plain-text list, one item per line, then the total on its own line."
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
            "You may be given one or more photos (e.g. the error plus the "
            "relevant code, or multiple screenshots of the same issue). Combine "
            "info across all photos. Read this code error, stack trace, or code "
            "screenshot exactly as written. Transcribe the exact error message "
            "(word for word) and any visible code faithfully. If the photo does "
            "NOT contain any code, error message, or stack trace, say clearly: "
            "'No code or error detected in this photo.' — do not invent one."
        ),
        "followup_label": "Anything else about your setup? (language, what you were trying to do) — optional",
        "search_query_template": "{vision_output} fix solution",
        "followup_prompt": (
            "Here is the error/code that was read from the image:\n{vision_output}\n\n"
            "Here is what a web search found about this exact error (use this for "
            "accurate, real fixes instead of guessing):\n{search_results}\n\n"
            "Extra context from the user:\n{user_input}\n\n"
            "Explain in plain, beginner-friendly English: (1) what this error means, "
            "(2) the most likely cause, (3) a step-by-step fix grounded in the real "
            "web search results above. Keep it clear and encouraging, no "
            "unnecessary jargon."
        ),
    },
    "🍳 Cook It": {
        "desc": "Photo of your fridge/pantry → a recipe from what you have",
        "vision_prompt": (
            "You may be given one or more photos (e.g. fridge + pantry, or "
            "several angles of the same shelf). Combine info across all photos "
            "into one list. Look at each photo of a fridge, pantry, or food "
            "package. List every food ingredient or item you can identify, as a "
            "clean bullet list. If any item has a visible brand name or product "
            "name (e.g. on a package), state it clearly on its own line starting "
            "with 'BRAND:'. Be specific but don't guess wildly at things you "
            "can't see clearly."
        ),
        "followup_label": "Any preferences? (e.g. vegetarian, quick meal, spicy) — optional",
        "search_query_template": "{vision_output} ingredients list nutrition facts",
        "followup_prompt": (
            "Here are the ingredients/items spotted in the photo:\n{vision_output}\n\n"
            "Here is what a web search found about the branded product(s), if any "
            "were identified (use this for accurate real ingredient info instead "
            "of guessing):\n{search_results}\n\n"
            "User preferences:\n{user_input}\n\n"
            "Suggest one simple, realistic recipe using mostly these ingredients. "
            "If a branded product was identified, use its REAL ingredients from "
            "the web search results above rather than assuming. Give a short "
            "ingredient list and clear numbered steps."
        ),
    },
}

# ---------- HELPERS ----------
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode("utf-8")


def run_vision(image_b64_list, prompt):
    content = [{"type": "text", "text": prompt}]
    for img_b64 in image_b64_list:
        content.append(
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
        )
    resp = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[{"role": "user", "content": content}],
        max_tokens=1500,
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

if image_source == "Upload":
    uploaded_files = st.file_uploader(
        "Upload one or more photos",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )
else:
    single_cam = st.camera_input("Take a photo")
    uploaded_files = [single_cam] if single_cam else []

if uploaded_files:
    cols = st.columns(min(len(uploaded_files), 3))
    for i, f in enumerate(uploaded_files):
        with cols[i % len(cols)]:
            st.image(f, caption=f"Photo {i+1}", use_container_width=True)

    if "vision_output" not in st.session_state:
        st.session_state.vision_output = None
    if "last_mode" not in st.session_state or st.session_state.last_mode != mode:
        st.session_state.vision_output = None
        st.session_state.last_mode = mode

    if st.session_state.vision_output is None:
        if st.button("🔍 Analyze photo(s)", type="primary"):
            with st.spinner(f"Reading {len(uploaded_files)} photo(s)..."):
                image_b64_list = [encode_image(f) for f in uploaded_files]
                st.session_state.vision_output = run_vision(
                    image_b64_list, MODES[mode]["vision_prompt"]
                )
            st.rerun()

    if st.session_state.vision_output:
        with st.expander("What the AI saw", expanded=False):
            st.write(st.session_state.vision_output)

        user_input = st.text_input(MODES[mode]["followup_label"], key=f"input_{mode}")

        if st.button("✨ Get my answer", type="primary"):
            search_results = "(no web search for this mode)"
            if "search_query_template" in MODES[mode]:
                with st.spinner("Searching the web for accurate info..."):
                    if user_input.strip():
                        # user typed a specific request — search that directly
                        query = user_input.strip()[:390]
                    else:
                        query = build_search_query(
                            st.session_state.vision_output,
                            MODES[mode]["search_query_template"],
                        )
                    search_results = web_search(query)
                with st.expander("What the web search found", expanded=False):
                    st.caption(f"Searched: {query}")
                    st.write(search_results)

            with st.spinner("Working it out..."):
                final_prompt = MODES[mode]["followup_prompt"].format(
                    vision_output=st.session_state.vision_output,
                    search_results=search_results,
                    user_input=user_input if user_input else "(none provided)",
                )
                answer = run_text(final_prompt)
            st.success("Done!")
            st.markdown(answer)
else:
    st.info("Upload or take a photo to get started 👆")
