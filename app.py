import io
import os
import re
from datetime import datetime
from pathlib import Path

import streamlit as st
from PIL import Image
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
   st.markdown("""
<style>
.stApp {
    background-color: #0B1120;
    color: white;
}

h1, h2, h3, p, label, span {
    color: white !important;
}

[data-testid="stSidebar"] {
    background-color: #111827;
}

.stButton > button {
    background: linear-gradient(90deg, #2563EB, #9333EA);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: bold;
}

[data-testid="stMetric"] {
    background-color: #1E293B;
    padding: 15px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)
    page_title="AI Word Agent",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
<style>

.stApp {
    background: #f4f7fb;
}

.block-container {
    max-width: 1500px;
    padding-top: 1.2rem;
}

[data-testid="stSidebar"] {
    background: #eef4ff;
}

.hero {
    background: linear-gradient(
        135deg,
        #2563eb 0%,
        #4f46e5 50%,
        #7c3aed 100%
    );
    color: white;
    padding: 28px;
    border-radius: 20px;
    margin-bottom: 20px;
    box-shadow: 0 10px 35px rgba(37,99,235,.20);
}

.hero h1 {
    margin: 0;
    font-size: 2.2rem;
}

.hero p {
    margin-top: 8px;
    opacity: .92;
}

.card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 5px 20px rgba(15,23,42,.05);
}

.ribbon {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 10px;
    margin: 10px 0 15px;
}

.document-title {
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 10px;
}

.stat-card {
    background: white;
    border-radius: 15px;
    padding: 15px;
    border: 1px solid #e5e7eb;
    text-align: center;
}

.small-text {
    color: #667085;
    font-size: 0.85rem;
}

div[data-testid="stButton"] button {
    border-radius: 10px;
    font-weight: 600;
}

div[data-testid="stDownloadButton"] button {
    border-radius: 10px;
    font-weight: 600;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# SESSION STATE
# =========================================================

def initialize_state():

    defaults = {
        "documents": {},
        "active_document": "Untitled",
        "history": [],
        "ai_result": "",
        "last_saved": None,
        "autosave": True,
        "show_image_upload": False,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


initialize_state()


# =========================================================
# DOCUMENT FUNCTIONS
# =========================================================

def create_document(name="Untitled"):

    return {
        "title": name,
        "content": """
<h1>Untitled Document</h1>

<p>Start writing your document here...</p>

<p>You can use HTML formatting such as:</p>

<ul>
<li><b>Bold text</b></li>
<li><i>Italic text</i></li>
<li><u>Underlined text</u></li>
</ul>
""",
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
    }


if not st.session_state.documents:

    st.session_state.documents["Untitled"] = create_document()


def current_document():

    return st.session_state.documents[
        st.session_state.active_document
    ]


def save_document(content):

    document = current_document()

    document["content"] = content

    document["updated"] = datetime.now().isoformat()

    st.session_state.last_saved = datetime.now().strftime(
        "%H:%M:%S"
    )

    st.session_state.history.append(
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "document": document["title"],
            "action": "Document updated",
        }
    )

    st.session_state.history = st.session_state.history[-50:]


# =========================================================
# TEXT FUNCTIONS
# =========================================================

def html_to_text(html):

    html = re.sub(
        r"<br\s*/?>",
        "\n",
        html,
        flags=re.IGNORECASE
    )

    html = re.sub(
        r"</(p|div|h1|h2|h3|h4|h5|h6|li)>",
        "\n",
        html,
        flags=re.IGNORECASE
    )

    html = re.sub(
        r"<li[^>]*>",
        "• ",
        html,
        flags=re.IGNORECASE
    )

    html = re.sub(
        r"<[^>]+>",
        "",
        html
    )

    html = html.replace("&nbsp;", " ")
    html = html.replace("&amp;", "&")
    html = html.replace("&lt;", "<")
    html = html.replace("&gt;", ">")

    return html.strip()


def count_words(text):

    return len(
        re.findall(
            r"\b[\w'-]+\b",
            text,
            flags=re.UNICODE
        )
    )


def count_characters(text):

    return len(text)


# =========================================================
# DOCX PAGE NUMBER
# =========================================================

def add_page_number(paragraph):

    run = paragraph.add_run()

    field_begin = OxmlElement("w:fldChar")
    field_begin.set(qn("w:fldCharType"), "begin")

    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = "PAGE"

    field_end = OxmlElement("w:fldChar")
    field_end.set(qn("w:fldCharType"), "end")

    run._r.append(field_begin)
    run._r.append(instruction)
    run._r.append(field_end)


# =========================================================
# HTML → DOCX
# =========================================================

def html_to_docx(html):

    document = Document()

    for section in document.sections:

        section.top_margin = Inches(0.7)
        section.bottom_margin = Inches(0.7)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

        footer = section.footer.paragraphs[0]

        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER

        footer.add_run("Page ")

        add_page_number(footer)

    blocks = re.findall(
        r"<(h[1-6]|p|li|blockquote|div)[^>]*>(.*?)</\1>",
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    if not blocks:

        blocks = [("p", html)]

    for tag, content in blocks:

        paragraph = document.add_paragraph()

        tag = tag.lower()

        if tag == "li":

            paragraph.style = document.styles["List Bullet"]

        elif tag == "blockquote":

            paragraph.style = document.styles["Intense Quote"]

        text = re.sub(
            r"<[^>]+>",
            "",
            content
        )

        text = (
            text
            .replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
        )

        run = paragraph.add_run(text)

        if tag in ["h1", "h2", "h3", "h4"]:

            run.bold = True

            sizes = {
                "h1": 24,
                "h2": 19,
                "h3": 16,
                "h4": 14,
            }

            run.font.size = Pt(sizes[tag])

        else:

            run.font.size = Pt(12)

    return document


def create_docx(html):

    document = html_to_docx(html)

    output = io.BytesIO()

    document.save(output)

    output.seek(0)

    return output.getvalue()


# =========================================================
# DOCX IMPORT
# =========================================================

def import_docx(file):

    document = Document(file)

    html_parts = []

    for paragraph in document.paragraphs:

        text = paragraph.text.strip()

        if not text:
            continue

        style = ""

        if paragraph.style:

            style = paragraph.style.name

        if style.startswith("Heading 1"):

            html_parts.append(
                f"<h1>{text}</h1>"
            )

        elif style.startswith("Heading 2"):

            html_parts.append(
                f"<h2>{text}</h2>"
            )

        elif "List" in style:

            html_parts.append(
                f"<li>{text}</li>"
            )

        else:

            html_parts.append(
                f"<p>{text}</p>"
            )

    # Tables

    for table in document.tables:

        html_parts.append("<table border='1'>")

        for row in table.rows:

            html_parts.append("<tr>")

            for cell in row.cells:

                html_parts.append(
                    f"<td>{cell.text}</td>"
                )

            html_parts.append("</tr>")

        html_parts.append("</table>")

    if not html_parts:

        return "<p>Imported document is empty.</p>"

    return "\n".join(html_parts)


# =========================================================
# PDF EXPORT
# =========================================================

def create_pdf(html, title):

    output = io.BytesIO()

    pdf = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=50,
        bottomMargin=50,
        title=title,
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="Justified",
            parent=styles["BodyText"],
            alignment=TA_JUSTIFY,
            leading=17,
        )
    )

    story = []

    blocks = re.findall(
        r"<(h1|h2|h3|p|li|blockquote)[^>]*>(.*?)</\1>",
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    if not blocks:

        blocks = [("p", html)]

    for tag, content in blocks:

        text = re.sub(
            r"<[^>]+>",
            "",
            content
        )

        text = (
            text
            .replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
        )

        tag = tag.lower()

        if tag == "h1":

            style = styles["Title"]

        elif tag == "h2":

            style = styles["Heading2"]

        elif tag == "h3":

            style = styles["Heading3"]

        else:

            style = styles["Justified"]

        if tag == "li":

            text = "• " + text

        story.append(
            Paragraph(text, style)
        )

        story.append(
            Spacer(1, 8)
        )

    pdf.build(story)

    output.seek(0)

    return output.getvalue()


# =========================================================
# AI FUNCTIONS
# =========================================================

def get_openai_client():

    api_key = None

    try:

        api_key = st.secrets.get(
            "OPENAI_API_KEY"
        )

    except Exception:

        pass

    if not api_key:

        api_key = os.getenv(
            "OPENAI_API_KEY"
        )

    if not api_key:

        return None

    if OpenAI is None:

        return None

    return OpenAI(api_key=api_key)


def ai_assistant(action, text):

    client = get_openai_client()

    if client is None:

        return None, (
            "OpenAI API key configure nahi hai. "
            "Normal document editor phir bhi work karega."
        )

    if not text.strip():

        return None, "Please pehle kuch text enter karein."

    instructions = {

        "Improve":
            "Improve this text professionally while keeping the same meaning.",

        "Rewrite":
            "Rewrite this text in a clear and professional style.",

        "Summarize":
            "Create a concise summary of this text.",

        "Grammar":
            "Correct grammar, spelling, punctuation and awkward wording.",

    }

    try:

        response = client.chat.completions.create(

            model="gpt-4o-mini",

            messages=[
                {
                    "role": "system",
                    "content":
                    "You are a professional document writing assistant."
                },
                {
                    "role": "user",
                    "content":
                    instructions[action]
                    + "\n\nTEXT:\n"
                    + text
                }
            ],

            temperature=0.4,
        )

        return (
            response.choices[0].message.content.strip(),
            None
        )

    except Exception as error:

        return None, f"AI error: {error}"


# =========================================================
# TEMPLATES
# =========================================================

TEMPLATES = {

    "Blank Document":
        """
<h1>Untitled Document</h1>

<p>Start writing here...</p>
""",

    "CV / Resume":
        """
<h1>Your Name</h1>

<p><b>Professional Title</b></p>

<p>Email | Phone | City | LinkedIn</p>

<h2>Professional Summary</h2>

<p>
Write your professional summary here.
</p>

<h2>Education</h2>

<p>
Degree — University — Year
</p>

<h2>Experience</h2>

<p>
<b>Job Title — Company</b>
</p>

<p>
Describe your responsibilities and achievements.
</p>

<h2>Skills</h2>

<ul>
<li>Communication</li>
<li>Microsoft Office</li>
<li>Graphic Design</li>
</ul>
""",

    "Application":
        """
<p>Date: __________________</p>

<p>
To,<br>
The Principal / Manager<br>
Organization Name
</p>

<h2>
Subject: Application for __________________
</h2>

<p>
Respected Sir/Madam,
</p>

<p>
I respectfully request that you consider my application
for the above-mentioned matter.
</p>

<p>
Thank you for your consideration.
</p>

<p>
Sincerely,<br>
Your Name
</p>
""",

    "Formal Letter":
        """
<p>Date: __________________</p>

<p>Dear Sir/Madam,</p>

<h2>Subject: __________________</h2>

<p>
Write your formal letter here.
Keep the language clear and professional.
</p>

<p>
Yours sincerely,<br>
Your Name
</p>
""",

    "Project Report":
        """
<h1>Project Report</h1>

<h2>Introduction</h2>

<p>
Write the introduction of your project here.
</p>

<h2>Objectives</h2>

<ul>
<li>Objective One</li>
<li>Objective Two</li>
<li>Objective Three</li>
</ul>

<h2>Methodology</h2>

<p>
Describe your project methodology here.
</p>

<h2>Findings</h2>

<p>
Write your findings here.
</p>

<h2>Conclusion</h2>

<p>
Write your conclusion here.
</p>
""",
}


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
        text-align:center;
        padding:10px;
        ">
        <h2>📝 AI Word Agent</h2>
        <p>Smart Document Studio</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "🏠 Home",
            "📄 Document Editor",
            "🤖 AI Assistant",
            "📋 Templates",
            "🕘 History",
        ]
    )

    st.divider()

    st.markdown("### 📂 Documents")

    document_names = list(
        st.session_state.documents.keys()
    )

    selected_document = st.selectbox(
        "Open Document",
        document_names,
        index=document_names.index(
            st.session_state.active_document
        )
    )

    if (
        selected_document
        != st.session_state.active_document
    ):

        st.session_state.active_document = (
            selected_document
        )

        st.rerun()

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "＋ New",
            use_container_width=True
        ):

            number = 1

            new_name = "Untitled"

            while new_name in st.session_state.documents:

                new_name = f"Untitled {number}"

                number += 1

            st.session_state.documents[
                new_name
            ] = create_document(new_name)

            st.session_state.active_document = new_name

            st.rerun()

    with col2:

        if st.button(
            "🗑 Delete",
            use_container_width=True
        ):

            if len(st.session_state.documents) > 1:

                del st.session_state.documents[
                    st.session_state.active_document
                ]

                st.session_state.active_document = (
                    next(
                        iter(
                            st.session_state.documents
                        )
                    )
                )

                st.rerun()

            else:

                st.warning(
                    "Kam az kam ek document hona zaroori hai."
                )

    st.divider()

    st.checkbox(
        "Autosave",
        value=True,
        key="autosave"
    )

    if st.session_state.last_saved:

        st.caption(
            f"Last saved: {st.session_state.last_saved}"
        )


# =========================================================
# HOME
# =========================================================

if page == "🏠 Home":

    st.markdown(
        """
        <div class="hero">

        <h1>
        📝 AI Word Agent
        </h1>

        <p>
        Smart Document Studio — Write, Format,
        Improve and Export Professional Documents.
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)

    cards = [
        (
            "📄",
            "Create",
            "Professional documents create karein."
        ),
        (
            "🎨",
            "Format",
            "Text, headings, lists aur tables format karein."
        ),
        (
            "🤖",
            "AI Assistant",
            "Writing aur grammar improve karein."
        ),
        (
            "📤",
            "Export",
            "DOCX aur PDF download karein."
        ),
    ]

    for col, card in zip(
        [col1, col2, col3, col4],
        cards
    ):

        with col:

            icon, title, description = card

            st.markdown(
                f"""
                <div class="card">

                <h3>
                {icon} {title}
                </h3>

                <p>
                {description}
                </p>

                </div>
                """,
                unsafe_allow_html=True
            )

    st.write("")

    st.info(
        "Left sidebar se Document Editor open karein "
        "aur apna document banana start karein."
    )


# =========================================================
# DOCUMENT EDITOR
# =========================================================

elif page == "📄 Document Editor":

    document = current_document()

    st.markdown(
        f"""
        <div class="document-title">
        📄 {document["title"]}
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------------- Ribbon ----------------

    st.markdown(
        '<div class="ribbon">',
        unsafe_allow_html=True
    )

    c1, c2, c3, c4, c5, c6, c7 = st.columns(
        [1, 1, 1, 1.2, 1.4, 1.4, 1.5]
    )

    with c1:

        bold = st.checkbox("B")

    with c2:

        italic = st.checkbox("I")

    with c3:

        underline = st.checkbox("U")

    with c4:

        font_size = st.number_input(
            "Font Size",
            min_value=8,
            max_value=72,
            value=12
        )

    with c5:

        text_color = st.color_picker(
            "Text Color",
            "#111827"
        )

    with c6:

        highlight = st.color_picker(
            "Highlight",
            "#fff59d"
        )

    with c7:

        alignment = st.selectbox(
            "Alignment",
            [
                "Left",
                "Center",
                "Right",
                "Justify"
            ]
        )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    # ---------------- Quick Tools ----------------

    q1, q2, q3, q4, q5, q6 = st.columns(6)

    with q1:

        if st.button(
            "🔗 Hyperlink",
            use_container_width=True
        ):

            st.info(
                "HTML editor mein <a href='URL'>Text</a> use karein."
            )

    with q2:

        if st.button(
            "▦ Table",
            use_container_width=True
        ):

            document["content"] += """
<table border="1">
<tr>
<th>Name</th>
<th>Details</th>
</tr>

<tr>
<td>Example</td>
<td>Information</td>
</tr>
</table>
"""

            st.success("Table insert ho gaya.")

    with q3:

        if st.button(
            "🖼 Image",
            use_container_width=True
        ):

            st.session_state.show_image_upload = True

    with q4:

        if st.button(
            "💾 Save",
            use_container_width=True
        ):

            st.session_state.last_saved = (
                datetime.now().strftime("%H:%M:%S")
            )

            st.success(
                "Document successfully save ho gaya."
            )

    with q5:

        st.download_button(
            "⬇ DOCX",
            data=create_docx(
                document["content"]
            ),
            file_name=f"{document['title']}.docx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            use_container_width=True
        )

    with q6:

        st.download_button(
            "📕 PDF",
            data=create_pdf(
                document["content"],
                document["title"]
            ),
            file_name=f"{document['title']}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # ---------------- Image Upload ----------------

    if st.session_state.show_image_upload:

        image_file = st.file_uploader(
            "Upload image",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp"
            ]
        )

        if image_file:

            try:

                image = Image.open(image_file)

                st.image(
                    image,
                    width=300
                )

                st.success(
                    "Image successfully upload ho gayi."
                )

            except Exception:

                st.error(
                    "Invalid image file."
                )

    # ---------------- Editor ----------------

    st.markdown("### ✍️ Document Editor")

    st.caption(
        "Neeche HTML editor hai. Is mein rich formatting, "
        "links, tables aur headings use ki ja sakti hain."
    )

    edited_content = st.text_area(
        "Document Content",
        value=document["content"],
        height=430,
        key=f"editor_{st.session_state.active_document}"
    )

    if st.button(
        "✨ Apply Changes",
        type="primary"
    ):

        save_document(
            edited_content
        )

        st.success(
            "Document changes apply ho gaye."
        )

        st.rerun()

    # ---------------- Preview ----------------

    st.markdown("### 👁️ Document Preview")

    st.markdown(
        document["content"],
        unsafe_allow_html=True
    )

    # ---------------- Statistics ----------------

    plain_text = html_to_text(
        document["content"]
    )

    st.markdown("### 📊 Document Statistics")

    s1, s2, s3 = st.columns(3)

    with s1:

        st.metric(
            "Words",
            count_words(plain_text)
        )

    with s2:

        st.metric(
            "Characters",
            count_characters(plain_text)
        )

    with s3:

        st.metric(
            "Paragraphs",
            len(
                [
                    x
                    for x in plain_text.split("\n")
                    if x.strip()
                ]
            )
        )

    # ---------------- Find Replace ----------------

    st.divider()

    st.markdown("### 🔎 Find & Replace")

    f1, f2, f3 = st.columns(
        [2, 2, 1]
    )

    with f1:

        find_text = st.text_input(
            "Find"
        )

    with f2:

        replace_text = st.text_input(
            "Replace With"
        )

    with f3:

        if st.button(
            "Replace All",
            use_container_width=True
        ):

            if find_text:

                new_content = document[
                    "content"
                ].replace(
                    find_text,
                    replace_text
                )

                save_document(
                    new_content
                )

                st.success(
                    "All matching text replace ho gaya."
                )

                st.rerun()

            else:

                st.warning(
                    "Find field mein text enter karein."
                )

    # ---------------- Page Layout ----------------

    st.divider()

    st.markdown("### 📐 Page Layout")

    p1, p2, p3 = st.columns(3)

    with p1:

        st.selectbox(
            "Paper Size",
            [
                "A4",
                "Letter",
                "Legal"
            ]
        )

    with p2:

        st.selectbox(
            "Orientation",
            [
                "Portrait",
                "Landscape"
            ]
        )

    with p3:

        st.selectbox(
            "Margins",
            [
                "Normal",
                "Narrow",
                "Wide"
            ]
        )

    # ---------------- Import DOCX ----------------

    st.divider()

    st.markdown("### 📥 Import DOCX")

    uploaded_docx = st.file_uploader(
        "DOCX file select karein",
        type=["docx"],
        key="docx_import"
    )

    if uploaded_docx:

        if st.button(
            "Import DOCX"
        ):

            try:

                imported_html = import_docx(
                    uploaded_docx
                )

                save_document(
                    imported_html
                )

                st.success(
                    "DOCX successfully import ho gaya."
                )

                st.rerun()

            except Exception as error:

                st.error(
                    f"DOCX import error: {error}"
                )


# =========================================================
# AI ASSISTANT
# =========================================================

elif page == "🤖 AI Assistant":

    st.markdown(
        """
        <div class="hero">

        <h1>
        🤖 AI Writing Assistant
        </h1>

        <p>
        Apne text ko improve, rewrite, summarize
        aur grammar-correct karein.
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    document = current_document()

    ai_text = st.text_area(
        "Text for AI Assistant",
        value=html_to_text(
            document["content"]
        ),
        height=300
    )

    action = st.selectbox(
        "Choose AI Action",
        [
            "Improve",
            "Rewrite",
            "Summarize",
            "Grammar"
        ]
    )

    if st.button(
        "✨ Run AI Assistant",
        type="primary"
    ):

        result, error = ai_assistant(
            action,
            ai_text
        )

        if error:

            st.warning(error)

        else:

            st.session_state.ai_result = result

    if st.session_state.ai_result:

        st.markdown("### ✨ AI Result")

        st.text_area(
            "Result",
            value=st.session_state.ai_result,
            height=300
        )

        c1, c2 = st.columns(2)

        with c1:

            if st.button(
                "Replace Document"
            ):

                new_html = (
                    "<p>"
                    + st.session_state.ai_result.replace(
                        "\n",
                        "</p><p>"
                    )
                    + "</p>"
                )

                save_document(
                    new_html
                )

                st.success(
                    "Document AI result se update ho gaya."
                )

        with c2:

            st.download_button(
                "⬇ Download AI Result",
                data=st.session_state.ai_result,
                file_name="ai_result.txt",
                mime="text/plain"
            )


# =========================================================
# TEMPLATES
# =========================================================

elif page == "📋 Templates":

    st.markdown(
        """
        <div class="hero">

        <h1>
        📋 Professional Templates
        </h1>

        <p>
        Ready-made templates use karke quickly document banayein.
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    for template_name, template_content in TEMPLATES.items():

        with st.container(border=True):

            col1, col2 = st.columns(
                [4, 1]
            )

            with col1:

                st.markdown(
                    f"### {template_name}"
                )

            with col2:

                if st.button(
                    "Use Template",
                    key=f"template_{template_name}"
                ):

                    document = current_document()

                    document["content"] = (
                        template_content
                    )

                    document["updated"] = (
                        datetime.now().isoformat()
                    )

                    st.success(
                        f"{template_name} loaded successfully."
                    )

                    st.rerun()


# =========================================================
# HISTORY
# =========================================================

elif page == "🕘 History":

    st.markdown(
        """
        <div class="hero">

        <h1>
        🕘 Document History
        </h1>

        <p>
        Current session ki recent document activities.
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    if not st.session_state.history:

        st.info(
            "Abhi koi document history available nahi hai."
        )

    else:

        for item in reversed(
            st.session_state.history
        ):

            st.write(
                f"**{item['time']}** — "
                f"{item['document']} — "
                f"{item['action']}"
            )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "AI Word Agent – Smart Document Studio | "
    "Python + Streamlit + python-docx + ReportLab + OpenAI"
)
