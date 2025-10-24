import os
import re
import yaml
from typing import Tuple, Dict, Any, List
from .SourcesRegistry import instantiate_sources, canonical_names

ENV_VAR_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")

def _sub_env(val: Any) -> Any:
    """Recursively substitute ${ENV} in strings from environment variables."""
    if isinstance(val, str):
        def repl(m):
            return os.environ.get(m.group(1), "")
        return ENV_VAR_PATTERN.sub(repl, val)
    if isinstance(val, dict):
        return {k: _sub_env(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_sub_env(v) for v in val]
    return val

def load_sources_from_yaml(path: str) -> Tuple[list, Dict[str, dict]]:
    """Load YAML config to build (source_instances, params_routing).

    Expected YAML structure:
    sources:
      enabled:
        OpenAlex: true
        arXiv: true
        ...
      defaults:
        OpenAlex:
          per_page: 200
          max_pages: 6
        arXiv:
          per_page: 200
          max_pages: 6
        PubMed:
          retmax: 200
          max_pages: 10
          term: ""
        IEEE Xplore:
          api_key: "${IEEE_API_KEY}"
          page_size: 100
          max_records: 200
        ...
    """
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    src_cfg = cfg.get("sources") or {}
    enabled_map = src_cfg.get("enabled") or {}
    defaults = src_cfg.get("defaults") or {}

    # env substitution in defaults
    defaults = _sub_env(defaults)

    srcs = instantiate_sources(enabled_map)
    # ensure defaults contain keys for all known sources, even if empty
    params: Dict[str, dict] = {}
    for name in canonical_names():
        params[name] = defaults.get(name, {})
    return srcs, params
