from typing import Dict, Type, List
# Import all implemented sources
from .OpenAlexSource import OpenAlexSource
from .ArxivSource import ArxivSource
from .PubMedSource import PubMedSource
from .CrossrefSource import CrossrefSource
from .BioRxivSource import BioRxivSource
from .MedRxivSource import MedRxivSource
from .HALSource import HALSource
from .IEEEXploreSource import IEEEXploreSource
from .OpenAIRESouce import OpenAIRESouce
from .SemanticScholarSource import SemanticScholarSource
from .DBLPSource import DBLPSource
from .EuropePMCSource import EuropePMCSource
from .OpenReviewSource import OpenReviewSource
from .NasaADSSource import NASAADSSource
from .DataCiteSource import DataCiteSource
from .CORESource import CORESource
from .DOAJSource import DOAJSource

# Registry maps human config keys to (class, canonical name string used in params routing)
REGISTRY: Dict[str, object] = {
    "OpenAlex": OpenAlexSource,
    "arXiv": ArxivSource,
    "PubMed": PubMedSource,
    "Crossref": CrossrefSource,
    "bioRxiv": BioRxivSource,
    "medRxiv": MedRxivSource,
    "HAL": HALSource,
    "IEEE Xplore": IEEEXploreSource,
    "OpenAIRE": OpenAIRESouce,
    "Semantic Scholar": SemanticScholarSource,
    "DBLP": DBLPSource,
    "Europe PMC": EuropePMCSource,
    "OpenReview": OpenReviewSource,
    "NASA ADS": NASAADSSource,
    "DataCite": DataCiteSource,
    "CORE": CORESource,
    "DOAJ": DOAJSource,
}

def instantiate_sources(enabled_map: dict) -> list:
    """Instantiate sources whose config 'enabled' is truthy."""
    instances = []
    for key, flag in enabled_map.items():
        if not flag:
            continue
        cls = REGISTRY.get(key)
        if cls is None:
            continue
        instances.append(cls())
    return instances

def canonical_names() -> list:
    return list(REGISTRY.keys())
