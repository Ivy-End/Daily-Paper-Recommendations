# actions/src/config_loader.py
import os, yaml
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, TypeVar
import logging

log = logging.getLogger(__name__)

ConfigType = TypeVar("ConfigType")

def LoadConfig(configPath: str) -> Dict[str, Any]:
    if not os.path.exists(configPath):
        raise FileNotFoundError(f"Config file not found: {configPath}")
    with open(configPath, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    if not isinstance(config, dict):
        raise ValueError("Config root must be a mapping (dict).")
    return config

def ReadConfig(configDict: Dict[str, Any], configKeys: List[str], default: ConfigType, coerce: Callable[[Any], ConfigType] | None) -> ConfigType:
    currentDict: Any = configDict
    for key in configKeys:
        if not isinstance(currentDict, dict) or key not in currentDict:
            return default
        currentDict = currentDict[key]
    if coerce is not None:
        try:
            return coerce(currentDict)
        except Exception:
            return default
    return currentDict if isinstance(currentDict, type(default)) else default

@dataclass
class Settings:
    # run
    TARGET_DATE : str
    TOP_K       : int
    EMBEDDING_MODEL   : str
    AI_ENABLE   : bool

    # zotero
    ZOTERO_USER : str
    ZOTERO_GROUP: str
    ZOTERO_KEY  : str

    # email
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASS: str
    SMTP_FROM: str
    SMTP_TO: str

    # ai
    GEMINI_KEY: str
    GEMINI_MODEL: str

def ParserConfig() -> Settings:
    log.info("Loading configuration from Config.yaml...")
    
    config = LoadConfig("Config.yaml")

    return Settings(
        # ---- run ----
        TARGET_DATE  = ReadConfig(config, ["run","TARGET_DATE"    ],                                       "",  str),
        TOP_K        = ReadConfig(config, ["run","TOP_K"          ],                                      100,  int),
        EMBEDDING_MODEL    = ReadConfig(config, ["run","EMBEDDING_MODEL"      ], "sentence-transformers/all-MiniLM-L6-v2",  str),
        AI_ENABLE    = ReadConfig(config, ["run","AI_ENABLE"      ],                                     True, bool),

        # ---- zotero ----
        ZOTERO_USER  = ReadConfig(config, ["zotero","ZOTERO_USER" ],                                       "",  str),
        ZOTERO_GROUP = ReadConfig(config, ["zotero","ZOTERO_GROUP"],                                       "",  str),
        ZOTERO_KEY   = ReadConfig(config, ["zotero","ZOTERO_KEY"  ],                                       "",  str),

        # ---- email ----
        SMTP_SERVER  = ReadConfig(config, ["email","SMTP_SERVER"  ],                                       "",  str),
        SMTP_PORT    = ReadConfig(config, ["email","SMTP_PORT"    ],                                      587,  int),
        SMTP_USER    = ReadConfig(config, ["email","SMTP_USERname"],                                       "",  str),
        SMTP_PASS    = ReadConfig(config, ["email","SMTP_PASSword"],                                       "",  str),
        SMTP_FROM    = ReadConfig(config, ["email","SMTP_FROM"    ],                                       "",  str),
        SMTP_TO      = ReadConfig(config, ["email","SMTP_TO"      ],                                       "",  str),

        # ---- ai (Gemini) ----
        GEMINI_KEY   = ReadConfig(config, ["ai","GEMINI_KEY"      ],                                       "",  str),
        GEMINI_MODEL = ReadConfig(config, ["ai","GEMINI_MODEL"    ],                  "models/gemini-2.5-pro",  str),
    )
