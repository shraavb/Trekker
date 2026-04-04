"""
JSON schemas for dashboard communication.

Pure Python dataclasses — no ROS dependency. Used by mqtt_bridge_node
and can be imported by external tools or tests.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum


class PatrolState(str, Enum):
    NAVIGATING = 'navigating'
    ARRIVED = 'arrived'
    CAPTURING = 'capturing'
    ANALYZING = 'analyzing'
    COMPLETE = 'complete'
    ERROR = 'error'


@dataclass
class PatrolStatus:
    waypoint_index: int
    total_waypoints: int
    state: str                # PatrolState value
    timestamp: str = ''       # ISO 8601

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> 'PatrolStatus':
        return cls(**json.loads(data))


@dataclass
class AnomalyReport:
    timestamp: str
    waypoint_id: int
    pose_x: float
    pose_y: float
    label: str
    confidence: float
    image_url: str = ''       # TODO: set when image upload is implemented
    bbox: list = None

    def __post_init__(self):
        if self.bbox is None:
            self.bbox = []

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> 'AnomalyReport':
        return cls(**json.loads(data))
