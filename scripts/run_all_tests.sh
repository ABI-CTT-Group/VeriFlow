#!/bin/bash
# Run all tests for VeriFlow

set -e

echo "=== Running Backend Tests ==="
cd backend
pip install -r requirements.txt -q
pytest tests/ -v
cd ..

echo ""
echo "=== Running Frontend Unit Tests ==="
cd ui
npm install --silent
npm run test:unit -- --run
cd ..

echo ""
echo "=== Running E2E Tests ==="
cd ui
npx playwright install chromium
npm run test:e2e
cd ..

echo ""
echo "=== All tests passed! ==="
