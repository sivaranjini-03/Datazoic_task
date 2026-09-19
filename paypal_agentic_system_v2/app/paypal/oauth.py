import time, base64, httpx
from app.config import settings

class OAuthManager:
    def __init__(self): self._token=None; self._expires_at=0.0
    async def get_token(self, force_refresh=False):
        if settings.paypal_mock_mode: return 'MOCK_ACCESS_TOKEN'
        if not force_refresh and self._token and time.time() < self._expires_at-60: return self._token
        if not settings.paypal_client_id or not settings.paypal_client_secret:
            raise RuntimeError('PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET are required when mock mode is disabled')
        basic=base64.b64encode(f'{settings.paypal_client_id}:{settings.paypal_client_secret}'.encode()).decode()
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as c:
            r=await c.post(f'{settings.paypal_base_url}/v1/oauth2/token',headers={'Authorization':f'Basic {basic}','Content-Type':'application/x-www-form-urlencoded'},data={'grant_type':'client_credentials'})
            r.raise_for_status(); d=r.json()
        self._token=d['access_token']; self._expires_at=time.time()+int(d.get('expires_in',900)); return self._token
