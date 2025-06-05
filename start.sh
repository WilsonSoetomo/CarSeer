#!/bin/bash

# Start the backend server
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000 &

# Start the frontend server
cd ../frontend
npm start &

# Wait for both processes
wait 