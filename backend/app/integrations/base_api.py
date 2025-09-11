import httpx
import time
from typing import Dict, Any, Optional
from app.models.sources import Source
from app.models.api_logs import APICallLog
from app.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

class BaseAPIClient:
    """Base class for all API integrations"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.session = httpx.AsyncClient()
        self.source = self._get_source()
        
    def _get_source(self) -> Source:
        """Get the source configuration from database"""
        db = SessionLocal()
        try:
            source = db.query(Source).filter(Source.name == self.source_name).first()
            if not source:
                raise ValueError(f"Source '{self.source_name}' not found in database")
            return source
        finally:
            db.close()
    
    async def _make_request(
        self, 
        endpoint: str, 
        method: str = "GET", 
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[Any, Any]:
        """Make API request with logging and error handling"""
        
        url = f"{self.source.api_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        start_time = time.time()
        
        # Prepare headers
        request_headers = headers or {}
        if self.source.request_headers:
            request_headers.update(self.source.request_headers)
        
        try:
            response = await self.session.request(
                method=method,
                url=url,
                params=params,
                headers=request_headers,
                timeout=30.0
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            # Log the API call
            self._log_api_call(
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                response_time_ms=response_time,
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                response.raise_for_status()
                
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            self._log_api_call(
                endpoint=endpoint,
                method=method,
                status_code=None,
                response_time_ms=int((time.time() - start_time) * 1000),
                params=params,
                error_message=str(e)
            )
            raise
    
    def _log_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: Optional[int],
        response_time_ms: int,
        params: Optional[Dict] = None,
        error_message: Optional[str] = None
    ):
        """Log API call to database"""
        db = SessionLocal()
        try:
            log_entry = APICallLog(
                source_id=self.source.source_id,
                endpoint=endpoint,
                http_method=method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                request_params=params,
                error_message=error_message
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log API call: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def close(self):
        """Close the HTTP session"""
        await self.session.aclose()