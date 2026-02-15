#!/bin/bash

echo "🎵 MoodLens Backend Setup Script"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "❌ Python 3 not found. Please install Python 3.10+"; exit 1; }

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check for .env
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    
    # Generate encryption key
    echo ""
    echo "Generating encryption key..."
    ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    
    # Update .env with generated key (macOS/Linux compatible)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/your-generated-fernet-key-here/$ENCRYPTION_KEY/" .env
    else
        sed -i "s/your-generated-fernet-key-here/$ENCRYPTION_KEY/" .env
    fi
    
    echo "✅ Encryption key generated and saved to .env"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add:"
    echo "   - SPOTIFY_CLIENT_ID (from Spotify Developer Dashboard)"
    echo "   - SPOTIFY_CLIENT_SECRET (from Spotify Developer Dashboard)"
    echo "   - JWT_SECRET_KEY (any random string)"
else
    echo ""
    echo "✅ .env file already exists"
fi

# Check Docker
echo ""
echo "Checking for Docker..."
if command -v docker &> /dev/null; then
    echo "✅ Docker found"
    echo ""
    echo "Starting PostgreSQL with Docker..."
    docker-compose up -d postgres
    echo "Waiting for PostgreSQL to be ready..."
    sleep 5
else
    echo "⚠️  Docker not found. Please install Docker or set up PostgreSQL manually."
    echo "   See SETUP.md for instructions."
fi

# Run migrations
echo ""
echo "Running database migrations..."
alembic upgrade head

echo ""
echo "=================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your Spotify credentials"
echo "2. Start the server: uvicorn app.main:app --reload"
echo "3. Open http://localhost:8000 to verify"
echo ""
echo "For detailed instructions, see SETUP.md"
echo "=================================="
