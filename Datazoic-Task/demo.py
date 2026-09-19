import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import agent

async def main():
    for sid,q in [('invoice-demo','Send an invoice for $50 to john@example.com'),('order-demo','Create an order for $100 and capture the payment')]:
        r=await agent.run(sid,q,False); print('\n',q,'\n',r)
        if r['status']=='confirmation_required': print('CONFIRMATION RESULT:',await agent.run(sid,q,True))
asyncio.run(main())
