#!/bin/bash
set -e
trap 'echo "❌ Failed at line $LINENO"' ERR

echo "🔧 Setting up FinTrak dev environment..."

# Install uv (Python package manager)
echo "📦 Installing uv..."
curl -LsSf https://astral.sh/uv/0.9.28/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Install Claude Code CLI
echo "📦 Installing Claude Code..."
npm install -g @anthropic-ai/claude-code

# Install OpenAI Codex CLI
echo "📦 Installing OpenAI Codex..."
npm install -g @openai/codex

# Install Speckit
echo "📦 Installing Speckit..."
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

# Setup Python environment
echo "🐍 Setting up Python environment..."
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r backend/requirements.txt

# Setup frontend
echo "⚛️ Setting up frontend..."
cd frontend && npm install && cd ..

echo "✅ Dev environment ready!"
echo ""
echo "Start the app with: ./fintrak"
