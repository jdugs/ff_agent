from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

class DataCapability(Enum):
    """Types of data capabilities"""
    PROJECTIONS = "projections"
    RANKINGS = "rankings"
    STATS = "stats"
    NEWS = "news"

@dataclass
class ProviderCapabilities:
    """Define what capabilities each provider has"""
    has_projections: bool = False
    has_rankings: bool = False
    has_stats: bool = False
    has_news: bool = False
    supports_weekly: bool = False
    supports_seasonal: bool = False
    weight: float = 1.0

# Core providers with their capabilities (no database dependency)
CORE_PROVIDERS = {
    'sleeper': ProviderCapabilities(
        has_projections=True,
        has_stats=True,
        supports_weekly=True,
        supports_seasonal=False,
        weight=0.85
    ),
    'fantasypros': ProviderCapabilities(
        has_projections=True,
        has_rankings=True,
        supports_weekly=True,
        supports_seasonal=True,
        weight=0.90
    ),
    'espn': ProviderCapabilities(
        has_projections=True,
        has_stats=True,
        supports_weekly=True,
        supports_seasonal=True,
        weight=0.80
    )
}

class ProviderManager:
    """Manages core data providers (no database dependency for core providers)"""
    
    def __init__(self):
        pass
    
    def get_providers(self) -> Dict[str, ProviderCapabilities]:
        """Get all core providers"""
        return CORE_PROVIDERS
    
    def get_provider_capabilities(self, provider_name: str) -> Optional[ProviderCapabilities]:
        """Get capabilities for a specific provider"""
        return CORE_PROVIDERS.get(provider_name.lower())
    
    def is_provider_available(self, provider_name: str) -> bool:
        """Check if a provider is available"""
        return provider_name.lower() in CORE_PROVIDERS
    
    def get_provider_weight(self, provider_name: str) -> float:
        """Get the weight/reliability score for a provider"""
        capabilities = CORE_PROVIDERS.get(provider_name.lower())
        return capabilities.weight if capabilities else 0.5
    
    def get_providers_with_capability(self, capability: DataCapability) -> List[str]:
        """Get list of providers that support a specific capability"""
        providers = []
        
        for provider_name, capabilities in CORE_PROVIDERS.items():
            # Check if provider supports the requested capability
            if capability == DataCapability.PROJECTIONS and capabilities.has_projections:
                providers.append(provider_name)
            elif capability == DataCapability.RANKINGS and capabilities.has_rankings:
                providers.append(provider_name)
            elif capability == DataCapability.STATS and capabilities.has_stats:
                providers.append(provider_name)
            elif capability == DataCapability.NEWS and capabilities.has_news:
                providers.append(provider_name)
        
        return providers
    
    def get_projection_providers(self) -> List[str]:
        """Get all providers that provide projections"""
        return self.get_providers_with_capability(DataCapability.PROJECTIONS)
    
    def get_ranking_providers(self) -> List[str]:
        """Get all providers that provide rankings"""
        return self.get_providers_with_capability(DataCapability.RANKINGS)
    
    def get_stats_providers(self) -> List[str]:
        """Get all providers that provide stats"""
        return self.get_providers_with_capability(DataCapability.STATS)