"""Service Map and Blast Radius for COSKA - Visual dependency graph and impact analysis."""

from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field
from enum import Enum
import structlog

logger = structlog.get_logger()


class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class DependencyType(str, Enum):
    CRITICAL = "critical"      # Failure causes complete outage
    DEGRADED = "degraded"      # Failure causes degraded functionality
    OPTIONAL = "optional"      # Failure has minimal impact


class ServiceNode(BaseModel):
    """Service in the dependency graph."""
    id: str
    name: str
    type: str  # api, database, cache, queue, external, gateway
    status: ServiceStatus = ServiceStatus.UNKNOWN
    metadata: Dict[str, Any] = Field(default_factory=dict)
    position: Optional[Dict[str, float]] = None  # x, y for visualization


class ServiceEdge(BaseModel):
    """Dependency edge between services."""
    id: str
    source: str  # service id
    target: str  # service id
    type: DependencyType = DependencyType.CRITICAL
    protocol: str = "http"  # http, grpc, redis, postgres, etc.
    latency_ms: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ServiceMap(BaseModel):
    """Complete service dependency map."""
    services: List[ServiceNode] = Field(default_factory=list)
    dependencies: List[ServiceEdge] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_service(self, service_id: str) -> Optional[ServiceNode]:
        for s in self.services:
            if s.id == service_id:
                return s
        return None
    
    def get_dependencies(self, service_id: str, direction: str = "outgoing") -> List[ServiceEdge]:
        """Get dependencies for a service."""
        if direction == "outgoing":
            return [e for e in self.dependencies if e.source == service_id]
        elif direction == "incoming":
            return [e for e in self.dependencies if e.target == service_id]
        return [e for e in self.dependencies if e.source == service_id or e.target == service_id]
    
    def get_dependents(self, service_id: str) -> List[ServiceNode]:
        """Get services that depend on this service (incoming edges)."""
        dependent_ids = {e.source for e in self.dependencies if e.target == service_id}
        return [s for s in self.services if s.id in dependent_ids]
    
    def get_dependencies_of(self, service_id: str) -> List[ServiceNode]:
        """Get services this service depends on (outgoing edges)."""
        dependency_ids = {e.target for e in self.dependencies if e.source == service_id}
        return [s for s in self.services if s.id in dependency_ids]


class BlastRadius(BaseModel):
    """Blast radius analysis for a service failure."""
    affected_service: str
    direct_dependencies: List[str] = Field(default_factory=list)
    transitive_dependencies: List[str] = Field(default_factory=list)
    impacted_services: List[Dict[str, Any]] = Field(default_factory=list)
    severity: str = "UNKNOWN"
    error_increase_percent: float = 0.0
    transaction_impact_percent: float = 0.0
    estimated_recovery_time_seconds: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Default service map for demo environment
DEFAULT_SERVICE_MAP = ServiceMap(
    services=[
        ServiceNode(
            id="client",
            name="Client Applications",
            type="client",
            status=ServiceStatus.HEALTHY,
            metadata={"description": "Web, mobile, and API clients"}
        ),
        ServiceNode(
            id="api-gateway",
            name="API Gateway",
            type="gateway",
            status=ServiceStatus.HEALTHY,
            metadata={"description": "Kong/NGINX ingress, rate limiting, auth"}
        ),
        ServiceNode(
            id="payment-api",
            name="Payment API",
            type="api",
            status=ServiceStatus.HEALTHY,
            metadata={
                "description": "Payment processing service",
                "slo_latency_p99_ms": 500,
                "slo_error_rate": 0.001,
                "slo_availability": 0.999
            }
        ),
        ServiceNode(
            id="checkout-api",
            name="Checkout API",
            type="api",
            status=ServiceStatus.HEALTHY,
            metadata={
                "description": "Order checkout orchestration",
                "slo_latency_p99_ms": 800,
                "slo_error_rate": 0.0005,
                "slo_availability": 0.9995
            }
        ),
        ServiceNode(
            id="order-api",
            name="Order API",
            type="api",
            status=ServiceStatus.HEALTHY,
            metadata={
                "description": "Order management and fulfillment",
                "slo_latency_p99_ms": 300,
                "slo_error_rate": 0.0001,
                "slo_availability": 0.9999
            }
        ),
        ServiceNode(
            id="inventory-api",
            name="Inventory API",
            type="api",
            status=ServiceStatus.HEALTHY,
            metadata={"description": "Product inventory management"}
        ),
        ServiceNode(
            id="catalog-api",
            name="Catalog API",
            type="api",
            status=ServiceStatus.HEALTHY,
            metadata={"description": "Product catalog and search"}
        ),
        ServiceNode(
            id="notification-api",
            name="Notification API",
            type="api",
            status=ServiceStatus.HEALTHY,
            metadata={"description": "Email, SMS, push notifications"}
        ),
        ServiceNode(
            id="postgresql",
            name="PostgreSQL Cluster",
            type="database",
            status=ServiceStatus.HEALTHY,
            metadata={
                "description": "Primary database (payments, orders, users)",
                "max_connections": 100,
                "pool_size": 30
            }
        ),
        ServiceNode(
            id="redis",
            name="Redis Cache",
            type="cache",
            status=ServiceStatus.HEALTHY,
            metadata={"description": "Distributed cache layer"}
        ),
        ServiceNode(
            id="stripe",
            name="Stripe Payment Provider",
            type="external",
            status=ServiceStatus.HEALTHY,
            metadata={"description": "External payment processor"}
        ),
        ServiceNode(
            id="message-queue",
            name="Message Queue (Kafka)",
            type="queue",
            status=ServiceStatus.HEALTHY,
            metadata={"description": "Event streaming platform"}
        ),
    ],
    dependencies=[
        # Client -> Gateway
        ServiceEdge(id="e1", source="client", target="api-gateway", type=DependencyType.CRITICAL, protocol="https"),
        
        # Gateway -> Services
        ServiceEdge(id="e2", source="api-gateway", target="payment-api", type=DependencyType.CRITICAL, protocol="http"),
        ServiceEdge(id="e3", source="api-gateway", target="checkout-api", type=DependencyType.CRITICAL, protocol="http"),
        ServiceEdge(id="e4", source="api-gateway", target="order-api", type=DependencyType.CRITICAL, protocol="http"),
        ServiceEdge(id="e5", source="api-gateway", target="inventory-api", type=DependencyType.DEGRADED, protocol="http"),
        ServiceEdge(id="e6", source="api-gateway", target="catalog-api", type=DependencyType.DEGRADED, protocol="http"),
        ServiceEdge(id="e7", source="api-gateway", target="notification-api", type=DependencyType.OPTIONAL, protocol="http"),
        
        # Checkout -> Payment (critical)
        ServiceEdge(id="e8", source="checkout-api", target="payment-api", type=DependencyType.CRITICAL, protocol="http", latency_ms=50),
        
        # Order -> Checkout, Payment (critical)
        ServiceEdge(id="e9", source="order-api", target="checkout-api", type=DependencyType.CRITICAL, protocol="http", latency_ms=30),
        ServiceEdge(id="e10", source="order-api", target="payment-api", type=DependencyType.CRITICAL, protocol="http", latency_ms=40),
        
        # Services -> PostgreSQL
        ServiceEdge(id="e11", source="payment-api", target="postgresql", type=DependencyType.CRITICAL, protocol="postgresql", latency_ms=5),
        ServiceEdge(id="e12", source="checkout-api", target="postgresql", type=DependencyType.CRITICAL, protocol="postgresql", latency_ms=5),
        ServiceEdge(id="e13", source="order-api", target="postgresql", type=DependencyType.CRITICAL, protocol="postgresql", latency_ms=5),
        ServiceEdge(id="e14", source="inventory-api", target="postgresql", type=DependencyType.CRITICAL, protocol="postgresql", latency_ms=5),
        
        # Services -> Redis
        ServiceEdge(id="e15", source="payment-api", target="redis", type=DependencyType.DEGRADED, protocol="redis", latency_ms=2),
        ServiceEdge(id="e16", source="checkout-api", target="redis", type=DependencyType.DEGRADED, protocol="redis", latency_ms=2),
        ServiceEdge(id="e17", source="catalog-api", target="redis", type=DependencyType.CRITICAL, protocol="redis", latency_ms=2),
        ServiceEdge(id="e18", source="order-api", target="redis", type=DependencyType.DEGRADED, protocol="redis", latency_ms=2),
        
        # Payment -> Stripe (critical for payments)
        ServiceEdge(id="e19", source="payment-api", target="stripe", type=DependencyType.CRITICAL, protocol="https", latency_ms=200),
        
        # Notification -> Message Queue
        ServiceEdge(id="e20", source="notification-api", target="message-queue", type=DependencyType.CRITICAL, protocol="kafka"),
        
        # Inventory -> Message Queue
        ServiceEdge(id="e21", source="inventory-api", target="message-queue", type=DependencyType.DEGRADED, protocol="kafka"),
    ],
    metadata={
        "environment": "production",
        "region": "us-east-1",
        "last_updated": "2026-10-30T00:00:00Z"
    }
)


class ServiceMapEngine:
    """Service map and blast radius analysis engine."""
    
    def __init__(self, service_map: Optional[ServiceMap] = None):
        self.service_map = service_map or DEFAULT_SERVICE_MAP
        # Build adjacency for fast traversal
        self._build_adjacency()
    
    def _build_adjacency(self):
        self._outgoing: Dict[str, List[ServiceEdge]] = {}
        self._incoming: Dict[str, List[ServiceEdge]] = {}
        
        for edge in self.service_map.dependencies:
            self._outgoing.setdefault(edge.source, []).append(edge)
            self._incoming.setdefault(edge.target, []).append(edge)
    
    def get_service_map(self) -> ServiceMap:
        """Get the complete service map."""
        return self.service_map
    
    def calculate_blast_radius(self, affected_service_id: str) -> BlastRadius:
        """Calculate blast radius for a service failure."""
        affected = self.service_map.get_service(affected_service_id)
        if not affected:
            return BlastRadius(
                affected_service=affected_service_id,
                severity="UNKNOWN",
                metadata={"error": "Service not found"}
            )
        
        # Direct dependencies (what this service depends on)
        direct_deps = self.service_map.get_dependencies_of(affected_service_id)
        direct_dep_ids = [s.id for s in direct_deps]
        
        # Transitive dependencies (dependencies of dependencies)
        transitive = self._get_transitive_dependencies(affected_service_id)
        
        # Impacted services (services that depend on this service - upstream impact)
        impacted = self._calculate_upstream_impact(affected_service_id)
        
        # Calculate severity based on dependency types
        critical_deps = [e for e in self._outgoing.get(affected_service_id, []) if e.type == DependencyType.CRITICAL]
        degraded_deps = [e for e in self._outgoing.get(affected_service_id, []) if e.type == DependencyType.DEGRADED]
        
        if critical_deps:
            severity = "CRITICAL"
        elif degraded_deps:
            severity = "HIGH"
        else:
            severity = "MEDIUM"
        
        # Estimate error increase and transaction impact
        error_increase = len(critical_deps) * 25 + len(degraded_deps) * 10
        transaction_impact = len(impacted) * 15
        
        return BlastRadius(
            affected_service=affected_service_id,
            direct_dependencies=direct_dep_ids,
            transitive_dependencies=transitive,
            impacted_services=impacted,
            severity=severity,
            error_increase_percent=min(error_increase, 100),
            transaction_impact_percent=min(transaction_impact, 100),
            estimated_recovery_time_seconds=self._estimate_recovery_time(affected_service_id, severity),
            metadata={
                "affected_service_name": affected.name,
                "critical_dependencies": len(critical_deps),
                "degraded_dependencies": len(degraded_deps),
                "total_impacted": len(impacted)
            }
        )
    
    def _get_transitive_dependencies(self, service_id: str, max_depth: int = 3) -> List[str]:
        """Get transitive dependencies up to max_depth."""
        visited = set()
        result = []
        
        def dfs(current: str, depth: int):
            if depth >= max_depth or current in visited:
                return
            visited.add(current)
            
            for edge in self._outgoing.get(current, []):
                if edge.target not in visited:
                    result.append(edge.target)
                    dfs(edge.target, depth + 1)
        
        dfs(service_id, 0)
        return list(set(result))
    
    def _calculate_upstream_impact(self, service_id: str) -> List[Dict[str, Any]]:
        """Calculate upstream impact (services that depend on this service)."""
        impacted = []
        visited = set()
        
        def dfs_upstream(current: str, path: List[str], depth: int):
            if depth > 5 or current in visited:
                return
            visited.add(current)
            
            for edge in self._incoming.get(current, []):
                source_service = self.service_map.get_service(edge.source)
                if source_service and source_service.id not in [p for p in path]:
                    impact_level = "CRITICAL" if edge.type == DependencyType.CRITICAL else \
                                  "DEGRADED" if edge.type == DependencyType.DEGRADED else "LOW"
                    
                    impacted.append({
                        "service_id": source_service.id,
                        "service_name": source_service.name,
                        "impact_level": impact_level,
                        "dependency_type": edge.type.value,
                        "path": " -> ".join(path + [source_service.name])
                    })
                    dfs_upstream(edge.source, path + [source_service.name], depth + 1)
        
        dfs_upstream(service_id, [affected.name], 0)
        return impacted
    
    def _estimate_recovery_time(self, service_id: str, severity: str) -> int:
        """Estimate recovery time based on service type and severity."""
        service = self.service_map.get_service(service_id)
        if not service:
            return 300
        
        base_times = {
            "api": 60,
            "database": 300,
            "cache": 30,
            "queue": 120,
            "external": 600,
            "gateway": 30,
        }
        
        base = base_times.get(service.type, 120)
        
        multipliers = {
            "CRITICAL": 2.0,
            "HIGH": 1.5,
            "MEDIUM": 1.0,
            "LOW": 0.5,
        }
        
        return int(base * multipliers.get(severity, 1.0))
    
    def get_service_status_overview(self) -> Dict[str, Any]:
        """Get overview of all service statuses."""
        return {
            "total_services": len(self.service_map.services),
            "healthy": len([s for s in self.service_map.services if s.status == ServiceStatus.HEALTHY]),
            "degraded": len([s for s in self.service_map.services if s.status == ServiceStatus.DEGRADED]),
            "critical": len([s for s in self.service_map.services if s.status == ServiceStatus.CRITICAL]),
            "unknown": len([s for s in self.service_map.services if s.status == ServiceStatus.UNKNOWN]),
            "services": [
                {
                    "id": s.id,
                    "name": s.name,
                    "type": s.type,
                    "status": s.status.value,
                    "dependents": len(self.service_map.get_dependents(s.id)),
                    "dependencies": len(self.service_map.get_dependencies_of(s.id))
                }
                for s in self.service_map.services
            ]
        }
    
    def update_service_status(self, service_id: str, status: ServiceStatus):
        """Update a service's status."""
        service = self.service_map.get_service(service_id)
        if service:
            service.status = status
            logger.info("service_status_updated", service_id=service_id, status=status.value)
    
    def to_cytoscape_elements(self) -> List[Dict[str, Any]]:
        """Convert to Cytoscape.js elements format."""
        elements = []
        
        # Status colors
        status_colors = {
            ServiceStatus.HEALTHY: "#44ff44",
            ServiceStatus.DEGRADED: "#ffaa44",
            ServiceStatus.CRITICAL: "#ff4444",
            ServiceStatus.UNKNOWN: "#888888",
        }
        
        # Type shapes
        type_shapes = {
            "client": "rectangle",
            "gateway": "diamond",
            "api": "ellipse",
            "database": "hexagon",
            "cache": "octagon",
            "queue": "vee",
            "external": "star",
        }
        
        for service in self.service_map.services:
            elements.append({
                "data": {
                    "id": service.id,
                    "label": service.name,
                    "type": service.type,
                    "status": service.status.value,
                    **service.metadata
                },
                "position": service.position or {"x": 0, "y": 0},
                "classes": f"service {service.type} {service.status.value}",
                "style": {
                    "background-color": status_colors.get(service.status, "#888"),
                    "shape": type_shapes.get(service.type, "ellipse"),
                }
            })
        
        for edge in self.service_map.dependencies:
            edge_color = {
                DependencyType.CRITICAL: "#ff4444",
                DependencyType.DEGRADED: "#ffaa44",
                DependencyType.OPTIONAL: "#44ff44",
            }.get(edge.type, "#888")
            
            elements.append({
                "data": {
                    "id": edge.id,
                    "source": edge.source,
                    "target": edge.target,
                    "type": edge.type.value,
                    "protocol": edge.protocol,
                    "latency_ms": edge.latency_ms,
                },
                "classes": f"dependency {edge.type.value}",
                "style": {
                    "line-color": edge_color,
                    "target-arrow-color": edge_color,
                    "width": 3 if edge.type == DependencyType.CRITICAL else (2 if edge.type == DependencyType.DEGRADED else 1),
                }
            })
        
        return elements


# Singleton
_service_map_engine: Optional[ServiceMapEngine] = None


def get_service_map_engine() -> ServiceMapEngine:
    global _service_map_engine
    if _service_map_engine is None:
        _service_map_engine = ServiceMapEngine()
    return _service_map_engine