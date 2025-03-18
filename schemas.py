import json
from typing import Any
from pydantic import BaseModel, field_validator


class SClient(BaseModel):
    comment: str
    email: str
    enable: bool
    expiryTime: int
    flow: str
    id: str
    limitIp: int
    reset: int
    subId: str
    tgId: str
    totalGB: int


class Settings(BaseModel):
    clients: list[SClient]
    decryption: str
    fallbacks: list[Any]


class RealitySubSettings(BaseModel):
    publicKey: str
    fingerprint: str
    serverName: str
    spiderX: str


class RealitySettings(BaseModel):
    show: bool
    xver: int
    dest: str
    serverNames: list[str]
    privateKey: str
    minClient: str
    maxClient: str
    maxTimediff: int
    shortIds: list[str]
    settings: RealitySubSettings


class TcpHeader(BaseModel):
    type: str


class TcpSettings(BaseModel):
    acceptProxyProtocol: bool
    header: TcpHeader


class SStreamSettings(BaseModel):
    network: str
    security: str
    externalProxy: list[Any]
    realitySettings: RealitySettings
    tcpSettings: TcpSettings


class Sniffing(BaseModel):
    enabled: bool
    destOverride: list[str]
    metadataOnly: bool
    routeOnly: bool


class Allocate(BaseModel):
    strategy: str
    refresh: int
    concurrency: int


class SInbound(BaseModel):
    id: int
    up: int
    down: int
    total: int
    remark: str
    enable: bool
    expiryTime: int
    clientStats: Any
    listen: str
    port: int
    protocol: str
    tag: str

    settings: Settings
    streamSettings: SStreamSettings
    sniffing: Sniffing
    allocate: Allocate

    @field_validator("settings", mode="before")
    def parse_settings(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("streamSettings", mode="before")
    def parse_stream_settings(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("sniffing", mode="before")
    def parse_sniffing(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("allocate", mode="before")
    def parse_allocate(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class Response(BaseModel):
    success: bool
    msg: str
    obj: SInbound | None


class Connection(BaseModel):
    inbound: int
    email: str
    connection_url: str
    host: str
