Property Sales Agent


python main_cli.py


test_lead_service.py 



curl -X POST http://127.0.0.1:8000/agents/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "c2e1f6a2-1c3a-4e9b-bb93-8f9a0e3d12ab",
    "message": "My budget is 1200000 usd. 3bhk. phuket. 350m"
  }'


curl -X POST http://127.0.0.1:8000/agents/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "c2e1f6a2-1c3a-4e9b-bb93-8f9a0e3d12ab",
    "message": "I want a 3 bhk in Dubai under 800000"
  }'

curl -X POST http://127.0.0.1:8000/agents/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "c2e1f6a2-1c3a-4e9b-bb93-8f9a0e3d12ab",
    "message": "I want a 5 bhk in Dubai under 27473303"
  }'

