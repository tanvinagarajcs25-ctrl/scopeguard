# ScopeGuard

An AI-powered agent that helps freelancers and small agencies detect scope creep by analyzing client requests against signed agreements (SOWs) and tracking cumulative out-of-scope work using long-term memory. It identifies unpaid extra work, learns from past client interactions and decisions, and generates professional change order drafts to help freelancers protect their time and revenue.

## Development Environment

### Requirements
- Python 3.14 (64-bit)
- pip (Python package manager)
- Git

### Setup

1. Clone the repository:
   ```bash
   git clone YOUR_REPOSITORY_URL
   cd scopeguard
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

3. Activate the virtual environment on Windows PowerShell:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

4. Install project dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```

5. Create a local `.env` file in the project root using `.env.example` as a reference.

6. Add your own API credentials to `.env`. Never commit this file to GitHub.

**Note:** This project currently uses Python 3.14 (64-bit). Team members should use the same version initially and report any dependency compatibility issues.