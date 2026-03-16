# AppInsight-MCP: Competitor Intelligence & Review Scraper

A lightweight, local-first tool designed to scrape App Store reviews, filter for negative sentiment, and generate "Gap Analysis" summaries using local LLMs. Built to be used as an MCP Server or a Skill for AI Coding Agents.

## 🚀 Core Features

### 1. Multi-Source Scraping
- **Input:** Fetch data using either `app_name` (automatic ID lookup) or direct `app_id`.
- **Target:** Apple App Store (extendable to Google Play).
- **Engine:** Reverse-engineered RSS/JSON feed requests (no API key required).

### 2. Precision Filtering
- **Rating Filter:** Specifically target 1 and 2-star reviews to find "pain points."
- **Temporal Filter:** Filter by date range (e.g., "only reviews from the last 30 days") to identify recent regressions or bugs.
- **Keyword Filtering:** Search for specific terms like "crash," "expensive," or "missing."

### 3. AI Analysis Modes (Prompt Templates)
- **Gap Finder Mode:** "Compare these reviews against my app's feature set and find what users are begging for."
- **Bug Hunter Mode:** "List the top 5 technical failures mentioned in these reviews."
- **Sentiment Shift Mode:** "How has the user sentiment changed since the competitor's last update?"

### 4. Agentic Integration (MCP/Skill)
- **MCP Server:** Implements the Model Context Protocol to allow LLMs to "call" the scraper as a tool.
- **Skill:** Exportable JSON-RPC or Python functions for integration with tools like Cursor or LangChain.

---

## 🛠 Technical Stack

- **Language:** Python 3.10+
- **Scraper:** `app-store-scraper` or custom `requests`-based RSS parser.
- **Local AI:** `Ollama` (running `phi3:mini` or `gemma:2b`).
- **Interface:** `mcp-python-sdk` for MCP server implementation.

---

## 📖 Usage Examples

### Python Snippet (Scraping & Filtering)
```python
from app_store_scraper import AppStore

def get_competitor_gaps(app_name, app_id):
    # 1. Scrape
    app = AppStore(country="us", app_name=app_name, app_id=app_id)
    app.review(how_many=200)
    
    # 2. Filter for 1-2 stars
    gaps = [r['review'] for r in app.reviews if r['rating'] <= 2]
    return gaps
```


### Competitor analysis
Analyzing the mcp-appstore repository, here are the technical gaps and opportunities for your custom solution.While it is a solid ASO (App Store Optimization) tool, it has several "product-centric" limitations that you can exploit to build a superior "Developer/Founder" tool.1. Gap: Rigid Sentiment AnalysisThe current MCP uses a tool called analyze_reviews, but it is opinionated and black-boxed. It returns fixed keys like sentimentBreakdown and keywordFrequency.Your Opportunity: Instead of returning a summary, your solution should return raw data chunks specifically for 1-2 star reviews. This allows your local LLM to perform "Deep Reasoning" (e.g., “Why exactly did the login fail for German users?”) rather than just seeing a generic "Negative: 5%" stat.2. Gap: Lack of Multi-App Comparative LogicThe existing tool is "Single-App" focused. To do what you want (gaining a competitive edge), you need to compare two apps side-by-side.Your Opportunity: Build a tool specifically named compare_competitors. It should fetch reviews for App A and App B simultaneously and use a "Difference Engine" prompt to highlight what App A has that App B users are complaining is missing.3. Gap: Filtering PrecisionThe AppReply MCP allows sorting by newest or helpfulness, but it lacks granular filtering before the AI sees the data.Your Opportunity: Implement a "Feature-Targeted Scrape." For example, "Fetch only 1-star reviews that contain the word 'payment' or 'subscription'." This reduces the token count for your local LLM and makes the summary 10x more relevant.4. Gap: Privacy & Local LLM IntegrationThe existing MCP is likely built to work with cloud-based models (like Claude).Your Opportunity: Since you want to use local LLMs, your MCP server can include an embedded inference engine (using Ollama-python or llama-cpp-python). This means the agent doesn't just get data; it gets a "Local Expert" that processed the data without any cloud API costs or privacy leaks.5. Technical Architecture Gap (Node.js vs Python)The existing project is written in Node.js.Your Opportunity: Since you are targeting AI/LLM work, building your version in Python is a strategic advantage. Most local LLM libraries (Ollama, PyTorch, Transformers) have better Python support, making it easier to integrate complex analysis modes later.Proposed Feature List for Your Custom MCPFeatureCustom Implementation IdeaTool: scrape_negativesReturns only 1-2 star reviews as a clean string for LLM context.Tool: find_feature_gapsCross-references negative reviews with a "positive features" list.Mode: local_summarizeA dedicated endpoint that triggers your local Phi-3/Gemma instance.FilteringAdd a since_date parameter to only see bugs in the latest app version.