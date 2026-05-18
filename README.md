# Agentic RAG

A web app for natural language question answering over personal documents using agentic retrieval.

## Setup

You'll need 2 terminals (1 for backend, 1 for frontend) and anaconda3 installed. Add a `.env` to `/backend` with your openai key (`.env.example` for reference). Add your langsmith key if you want to see how smart/dumb the retrieval agent is.

### Backend

```bash
# Create conda environment
conda create -n agentic-rag python=3.11
conda activate agentic-rag
# Install dependencies
pip install -r requirements.txt
# Start server
cd backend
python -m api.main
```
### Frontend 
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:3000. Load default documents and then click "Run Test" to run my test suite.

## Writeup
**What I built:**
Agentic RAG over a next.js frontend and FastAPI-Uvicorn backend that has a Langchain agent with a Chroma vector-search tool and a BM25 inspired keyword search tool. Honestly, a pretty standard Agentic RAG implementation with no special flourishes (aside from the pdf test docs).

**Why I built it**

- Picked agentic RAG since I've been doing a ton of agentic stuff and hybrid retrieval is too easy. Might as well pick the "shiniest best on-paper" option for an take-home interview
- Selected langchain, chroma, fastAPI, Uvicorn, conda as they're AI python staples I've used a ton for work + research
  - I had claude use one of my research repo's reference for how to use langchain/chroma in this context.
  - Dont hate me for using conda over docker, its just faster and easier
- Selected next.js frontend since raw html was too minimal and I've used next.js the most (out of frontend react frameworks)
- Picked md and txt first as theyre the easiest to extract/embed
- Targeted pdf since I had tons of lecture notes from my Neuroscience class and I wanted to use them as my test set
- Test passes if non-null/default string is returned + sources cited. 

**What I skipped:**

- Exhaustive tests
  - Probably my biggest skip but that's something you can pour hours into once you have a polished product that you want to put into prod. I was focusing on core functionality good enough first.
- Frontend is still ugly but I was focusing on core functionality > everything else
    - Some visual bugs in regards to text + uploaded documents. Would've been first fix after this commit
    - Managing uploaded files is nonexistent. Big feature that I skipped in order to have working pdf tests
    - Sources cited isnt tied to text sections but that requires more on agent output and frontend, way too much time
- Other file formats. It's harder and I only added pdf's because they were my test documents
- LLM-verified tests. Sources cited was enough to make sure it found something and it was probably right for my tests
- End to end tests. No way I'm doing those under this time limit

**What I'd tackle next**

- Squash aforementioned bugs
- Add good file management
- Upgrade testing and make them truly exhaustive and end-to-end
- Truly polish UI/UX (I actually have a knack for that, believe it or not)
- Play with agent component for optimal # of tool calls (short time vs enough data retrieved)
- Add other file formats
- dockerize for web deployment and then maybe do some web optimization
- A ton more I'd realize when really being in Arphie's shoes and thinking about the product/software/service

**Weakest part**
- Performance over big test set/ stress testing
  - I didnt have enough time to test really hard and I was using claude code. That means there are definitely flaws in my code and agentic RAG. I aimed for good enough over my test set and I feel like I delivered that in 2 hours.
  

**Misc.**
- I went slightly over 2 hours if we count time before inital commit, but 2 family members called me while I was working and I had bio breaks as well. I think I did genuinely follow that 2 hour limit pretty well.
- I used an informal tone because I felt it would be more readable and help you get a good gauge on my thought process.