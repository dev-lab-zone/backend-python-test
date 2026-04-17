import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from core.config import PROVIDER_URL, API_KEY
from core.logging_config import logger
from db.session import db

# --- Cliente HTTP Asíncrono ---
client = httpx.AsyncClient(
    timeout=10.0,
    headers={"X-API-Key": API_KEY}
)

# --- Lógica de Negocio y Resiliencia ---
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
    reraise=True
)
async def send_to_provider(payload: dict):
    """
    Envía la notificación al proveedor con lógica de reintentos para 429 y 500.
    """
    response = await client.post(PROVIDER_URL, json=payload)
    
    # Manejo específico de errores del provider (Rate limit 429 o Server Error 500)
    if response.status_code == 429:
        logger.warning("Rate limit alcanzado en el provider. Reintentando...")
        response.raise_for_status()
    elif response.status_code >= 500:
        logger.error(f"Error en el provider: {response.text}. Reintentando...")
        response.raise_for_status()
    
    response.raise_for_status()
    return response.json()

async def process_notification_task(request_id: str):
    """
    Tarea en segundo plano para procesar la notificación.
    """
    request_data = db.get(request_id)
    if not request_data:
        return

    db[request_id]["status"] = "processing"
    logger.info(f"Procesando solicitud {request_id}")

    try:
        # Extraer solo los campos que el provider espera
        payload = {
            "to": request_data["data"]["to"],
            "message": request_data["data"]["message"],
            "type": request_data["data"]["type"]
        }
        
        await send_to_provider(payload)
        db[request_id]["status"] = "sent"
        logger.info(f"Solicitud {request_id} enviada con éxito")
    except Exception as e:
        logger.error(f"Fallo definitivo al procesar {request_id}: {str(e)}")
        db[request_id]["status"] = "failed"
