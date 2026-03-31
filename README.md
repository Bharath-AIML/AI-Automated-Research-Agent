# 🔬 AI Automated Research Assistant

> A **multi-agent debate system** that automatically fetches, analyses, and critiques research papers using NLP and a three-agent adversarial pipeline.

---

## 📌 Overview

The AI Automated Research Assistant is a final-year Computer Science project (CCP) that demonstrates how multiple AI agents can collaborate to perform intelligent research critique. Given a topic, the system:

1. **Fetches** relevant papers from **arXiv** and **Semantic Scholar**
2. **Classifies** each sentence in the abstract using an NLP pipeline
3. **Debates** the paper quality through three specialised agents
4. **Renders** the full analysis in an interactive **Streamlit** dashboard

---

## 🏗️ Architecture

```
User Query
    │
    ▼
┌─────────────────────┐
│   Research Agent    │  ← Fetches papers from arXiv & Semantic Scholar
└────────┬────────────┘
         │  paper dict
         ▼
┌─────────────────────┐
│   NLP Pipeline      │  ← Preprocesses & classifies sentences
│  (Classifier +      │     into: Claim / Method / Result / Limitation
│   Preprocessor)     │
└────────┬────────────┘
         │  classified sentences
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│Defender│ │ Critic │  ← Adversarial agents debating the paper
└────┬───┘ └───┬────┘
     └────┬────┘
          ▼
     ┌─────────┐
     │  Judge  │  ← Synthesises both sides → Score (0–10) + Verdict
     └─────────┘
          │
          ▼
   Streamlit UI Dashboard
```

---

## 🤖 Agents

| Agent | Role | Output |
|-------|------|--------|
| **Defender** | Advocates for the paper — highlights strengths, strong results, and solid methodology | Arguments, key claims, overall positive stance |
| **Critic** | Acts as a sceptical reviewer — identifies weaknesses, vague methods, and missing sections | Criticisms, limitations, missing section flags |
| **Judge** | Final arbiter — weighs both sides and produces a balanced, scored verdict | Score (0–10), Verdict (Accept / Minor Revision / Major Revision / Reject), Recommendation |

### Verdict Scoring
| Score | Verdict |
|-------|---------|
| 8 – 10 | ✅ Accept |
| 5 – 7 | 🔄 Minor Revision |
| 3 – 4 | ⚠️ Major Revision |
| 0 – 2 | ❌ Reject |

---

## 📁 Project Structure

```
AI Automated Research Assistant/
│
├── app.py                  # Main Streamlit application (UI entry point)
├── config.py               # Central configuration (API settings, model, thresholds)
├── run.sh                  # Convenience launcher script
├── requirements.txt        # Python dependencies
├── PROJECT_OVERVIEW.txt    # Detailed project documentation
│
├── agents/
│   ├── controller.py       # Orchestrates the full debate pipeline
│   ├── research_agent.py   # Fetches papers from arXiv & Semantic Scholar
│   ├── defender_agent.py   # Generates supporting arguments
│   ├── critic_agent.py     # Generates critical arguments
│   └── judge_agent.py      # Produces the final scored verdict
│
├── nlp/
│   ├── classifier.py       # Sentence-level classifier (Claim/Method/Result/Limitation)
│   └── preprocessor.py     # Text cleaning and sentence splitting
│
└── utils/
    └── helpers.py          # Shared utility functions
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- pip

### 1. Clone the repository
```bash
git clone https://github.com/Bharath-AIML/AI-Automated-Research-Agent.git
cd AI-Automated-Research-Agent
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. (Optional) Download spaCy model
```bash
python -m spacy download en_core_web_sm
```

### 5. Run the app
```bash
bash run.sh
# OR directly:
streamlit run app.py
```

Then open **http://localhost:8501** in your browser.

---

## ⚙️ Configuration

All settings are centralised in [`config.py`](config.py):

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_RESULTS_PER_SOURCE` | `5` | Papers fetched per API source |
| `SENTENCE_CATEGORIES` | `[Claim, Method, Result, Limitation]` | NLP classification labels |
| `SENTENCE_TRANSFORMER_MODEL` | `all-MiniLM-L6-v2` | Embedding model for classification |
| `DEFENDER_TOP_N` / `CRITIC_TOP_N` | `5` | Top sentences each agent focuses on |
| `JUDGE_TOP_N` | `3` | Top arguments shown in verdict |
| `SEMANTIC_SCHOLAR_API_KEY` | *(blank)* | Optional API key for higher rate limits |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| UI | [Streamlit](https://streamlit.io/) + [Plotly](https://plotly.com/) |
| NLP | [spaCy](https://spacy.io/), [NLTK](https://www.nltk.org/), [sentence-transformers](https://www.sbert.net/) |
| ML | [scikit-learn](https://scikit-learn.org/), [Transformers (HuggingFace)](https://huggingface.co/) |
| Data | [arXiv API](https://arxiv.org/help/api), [Semantic Scholar API](https://api.semanticscholar.org/) |
| Core | Python 3.9+, NumPy, Pandas |

---

## 📊 NLP Pipeline

1. **Preprocessor** — cleans raw abstract text (removes LaTeX, normalises whitespace, splits into sentences)
2. **Classifier** — assigns each sentence one of four labels:
   - `Claim` — research hypothesis or contribution statement
   - `Method` — description of techniques or approaches used
   - `Result` — quantitative or qualitative findings
   - `Limitation` — acknowledged weaknesses or future work

Classification uses **sentence-transformer embeddings** (`all-MiniLM-L6-v2`) compared against category keyword anchors, producing a confidence score per sentence.

---

## 📄 License

This project is developed as an academic final-year project. Feel free to fork and build upon it.

---

## 👤 Author

**Bharath** — [GitHub](https://github.com/Bharath-AIML)
