#!/bin/bash
# Installation script for hs-mv-extractor

set -e

echo "🚀 Installing hs-mv-extractor..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.9+ is required, but found Python $python_version"
    exit 1
fi

echo "✅ Python $python_version detected"

# Install core dependencies
echo "📦 Installing core dependencies..."
pip3 install -r requirements.txt

# Install development dependencies (optional)
echo "📦 Installing development dependencies..."
pip3 install -r requirements-dev.txt

# Build and install the package
echo "🔨 Building and installing hs-mv-extractor..."
cd hs-mv-extractor
pip3 install -e .

echo "✅ Installation complete!"
echo ""
echo "🧪 To test the installation, run:"
echo "   python3 scripts/evaluation.py"
echo ""
echo "📖 For usage examples, see:"
echo "   python3 examples/basic_usage.py"