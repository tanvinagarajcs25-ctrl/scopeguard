# ScopeGuard - Development Process Log

This document records how our team uses AI tools
during the development of ScopeGuard.

## Development Log

| Date | Team Member | Task | AI Tool Used | Notes |
|------|-------------|------|--------------|-------|

## Memory Lead — Environment Setup

### Completed
- Installed Python 3.14 (64-bit).
- Created and activated the project's `.venv` virtual environment.
- Installed and verified required dependencies:
  - hindsight-client
  - fastapi
  - uvicorn
  - python-dotenv
  - groq
- Configured the local `.env` file and verified that it is ignored by Git.
- Created a Hindsight Cloud account and configured the correct Cloud API key.
- Created the memory bank `client-sharma-retail`.
- Created `backend/test_hindsight.py`.
- Successfully tested all three Hindsight operations:
  - RETAIN: Stored a sample client wishlist request.
  - RECALL: Retrieved the request and its relationship to the SOW.
  - REFLECT: Generated a contextual response using stored memory.

### Pending
- Implement reusable functions in `backend/memory.py`.
- Load the SOW and historical client messages.
- Implement contextual recall and pattern reflection.
- Integrate the memory module with `backend/agent.py`.
- Complete the memory ON/OFF evaluation.

### Technical notes
- Hindsight Cloud Base URL: `https://api.hindsight.vectorize.io`
- Memory bank: `client-sharma-retail`
- Python version: 3.14
- Smoke test: `python backend/test_hindsight.py`
- Result: All three Hindsight operations completed successfully.

## Data Lead - Teju

## Agent Lead - Ria