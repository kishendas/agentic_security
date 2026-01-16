#!/bin/bash

echo "🔐 Security Incident Knowledge Assistant - Setup Script"
echo "======================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check Node.js
echo "Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js $NODE_VERSION found${NC}"

echo ""
echo "📦 Setting up Backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  .env file not found. Creating...${NC}"
    read -p "Enter your OpenAI API key: " OPENAI_KEY
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    
    cat > .env << EOF
OPENAI_API_KEY=$OPENAI_KEY
SECRET_KEY=$SECRET_KEY
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Create data directory
mkdir -p data
echo -e "${GREEN}✓ Data directory ready${NC}"

cd ..

echo ""
echo "🎨 Setting up Frontend..."
cd frontend

# Install npm dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
else
    echo -e "${GREEN}✓ npm dependencies already installed${NC}"
fi

cd ..

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Start the backend:"
echo "   cd backend && source venv/bin/activate && python app.py"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   cd frontend && npm start"
echo ""
echo "3. Open http://localhost:3000 in your browser"
echo ""
echo "👥 Demo credentials:"
echo "   - security_admin / security123 (Full access)"
echo "   - engineer / engineer123 (KB + Logs)"
echo "   - sales_user / sales123 (KB only)"
echo ""
echo -e "${YELLOW}⚠️  Note: Make sure you have a valid OpenAI API key in backend/.env${NC}"
