"""Evidence Graph for COSKA - Graph-based evidence relationships and visualization."""

from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field
from enum import Enum
import uuid
import structlog

from app.models import Evidence, Hypothesis, Incident

logger = structlog.get_logger()


class EdgeType(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CAUSED_BY = "caused_by"
    RELATED_TO = "related_to"
    DERIVED_FROM = "derived_from"
    TESTED_BY = "tested_by"
    VERIFIED_BY = "verified_by"


class GraphNode(BaseModel):
    """Node in the evidence graph."""
    id: str
    type: str  # incident, evidence, hypothesis, root_cause, remediation, verification, service, document
    label: str
    data: Dict[str, Any] = Field(default_factory=dict)
    position: Optional[Dict[str, float]] = None  # x, y for visualization


class GraphEdge(BaseModel):
    """Edge in the evidence graph."""
    id: str
    source: str  # node id
    target: str  # node id
    type: EdgeType
    weight: float = 1.0
    label: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceGraph(BaseModel):
    """Complete evidence graph for an incident."""
    incident_id: str
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # For visualization
    layout: str = "hierarchical"  # hierarchical, force-directed, radial


class EvidenceGraphBuilder:
    """Builds evidence graph from investigation state."""
    
    def __init__(self):
        self.node_map: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
    
    def build(
        self,
        incident: Incident,
        evidence: List[Evidence],
        hypotheses: List[Hypothesis],
        root_cause: Optional[Dict[str, Any]] = None,
        remediation: Optional[Dict[str, Any]] = None,
        verification: Optional[Dict[str, Any]] = None,
        rag_documents: Optional[List[Dict[str, Any]]] = None
    ) -> EvidenceGraph:
        """Build complete evidence graph."""
        self.node_map = {}
        self.edges = []
        
        # 1. Incident node (root)
        self._add_node(GraphNode(
            id=f"incident-{incident.id}",
            type="incident",
            label=incident.id,
            data={
                "service": incident.service,
                "severity": incident.severity.value,
                "description": incident.description,
                "status": incident.status.value
            }
        ))
        
        # 2. Service node
        self._add_node(GraphNode(
            id=f"service-{incident.service}",
            type="service",
            label=incident.service,
            data={"type": "service"}
        ))
        self._add_edge(GraphEdge(
            id=f"edge-incident-service",
            source=f"incident-{incident.id}",
            target=f"service-{incident.service}",
            type=EdgeType.RELATED_TO,
            label="affects"
        ))
        
        # 3. Evidence nodes
        for ev in evidence:
            node_id = f"evidence-{ev.id}"
            self._add_node(GraphNode(
                id=node_id,
                type="evidence",
                label=ev.id,
                data={
                    "source_type": ev.source_type.value,
                    "claim": ev.claim,
                    "confidence": ev.confidence,
                    "related_component": ev.related_component,
                    "reference": ev.reference
                }
            ))
            # Connect evidence to incident
            self._add_edge(GraphEdge(
                id=f"edge-incident-{ev.id}",
                source=f"incident-{incident.id}",
                target=node_id,
                type=EdgeType.DERIVED_FROM,
                label="derived from"
            ))
            
            # Connect evidence to related component/service
            if ev.related_component:
                comp_id = f"component-{ev.related_component}"
                if comp_id not in self.node_map:
                    self._add_node(GraphNode(
                        id=comp_id,
                        type="component",
                        label=ev.related_component,
                        data={"type": "component"}
                    ))
                self._add_edge(GraphEdge(
                    id=f"edge-{ev.id}-{comp_id}",
                    source=node_id,
                    target=comp_id,
                    type=EdgeType.RELATED_TO,
                    label="references"
                ))
        
        # 4. Hypothesis nodes
        for hyp in hypotheses:
            node_id = f"hypothesis-{hyp.id}"
            self._add_node(GraphNode(
                id=node_id,
                type="hypothesis",
                label=hyp.id,
                data={
                    "title": hyp.title,
                    "description": hyp.description,
                    "confidence": hyp.confidence,
                    "status": hyp.status.value
                }
            ))
            
            # Connect hypothesis to incident
            self._add_edge(GraphEdge(
                id=f"edge-incident-{hyp.id}",
                source=f"incident-{incident.id}",
                target=node_id,
                type=EdgeType.DERIVED_FROM,
                label="hypothesizes"
            ))
            
            # Connect supporting evidence
            for ev_id in hyp.supporting_evidence_ids:
                self._add_edge(GraphEdge(
                    id=f"edge-{ev_id}-supports-{hyp.id}",
                    source=f"evidence-{ev_id}",
                    target=node_id,
                    type=EdgeType.SUPPORTS,
                    weight=hyp.confidence,
                    label=f"supports ({hyp.confidence:.0%})"
                ))
            
            # Connect contradicting evidence
            for ev_id in hyp.contradicting_evidence_ids:
                self._add_edge(GraphEdge(
                    id=f"edge-{ev_id}-contradicts-{hyp.id}",
                    source=f"evidence-{ev_id}",
                    target=node_id,
                    type=EdgeType.CONTRADICTS,
                    weight=hyp.confidence,
                    label=f"contradicts"
                ))
        
        # 5. Root cause node
        if root_cause:
            rc_id = "root-cause"
            self._add_node(GraphNode(
                id=rc_id,
                type="root_cause",
                label="ROOT CAUSE",
                data={
                    "cause": root_cause.get("root_cause", ""),
                    "confidence": root_cause.get("confidence", 0),
                    "uncertainty": root_cause.get("uncertainty")
                }
            ))
            
            # Connect to incident
            self._add_edge(GraphEdge(
                id="edge-incident-rootcause",
                source=f"incident-{incident.id}",
                target=rc_id,
                type=EdgeType.CAUSED_BY,
                label="caused by"
            ))
            
            # Connect supporting evidence
            for ev_id in root_cause.get("supporting_evidence_ids", []):
                self._add_edge(GraphEdge(
                    id=f"edge-{ev_id}-rootcause",
                    source=f"evidence-{ev_id}",
                    target=rc_id,
                    type=EdgeType.SUPPORTS,
                    label="supports root cause"
                ))
            
            # Connect rejected hypotheses
            for rh in root_cause.get("rejected_hypotheses", []):
                rh_id = rh.get("id")
                if rh_id:
                    self._add_edge(GraphEdge(
                        id=f"edge-{rh_id}-rejected",
                        source=f"hypothesis-{rh_id}",
                        target=rc_id,
                        type=EdgeType.CONTRADICTS,
                        label=f"rejected: {rh.get('reason', '')}"
                    ))
        
        # 6. Remediation node
        if remediation:
            rem_id = "remediation"
            self._add_node(GraphNode(
                id=rem_id,
                type="remediation",
                label="REMEDIATION",
                data={
                    "exact_change": remediation.get("exact_change", ""),
                    "description": remediation.get("description", ""),
                    "risk": remediation.get("risk", ""),
                    "rollback_plan": remediation.get("rollback_plan", "")
                }
            ))
            
            # Connect to root cause
            if root_cause:
                self._add_edge(GraphEdge(
                    id="edge-rootcause-remediation",
                    source="root-cause",
                    target=rem_id,
                    type=EdgeType.DERIVED_FROM,
                    label="remediates"
                ))
            
            # Connect to hypothesis
            if remediation.get("hypothesis_id"):
                self._add_edge(GraphEdge(
                    id=f"edge-hypothesis-remediation",
                    source=f"hypothesis-{remediation['hypothesis_id']}",
                    target=rem_id,
                    type=EdgeType.DERIVED_FROM,
                    label="addresses"
                ))
        
        # 7. Verification node
        if verification:
            ver_id = "verification"
            verdict = verification.get("verdict", "UNVERIFIED")
            self._add_node(GraphNode(
                id=ver_id,
                type="verification",
                label=f"VERIFICATION: {verdict}",
                data={
                    "verdict": verdict,
                    "baseline": verification.get("baseline_test"),
                    "post_fix": verification.get("post_fix_tests"),
                    "health": verification.get("health_check"),
                    "control": verification.get("control_test")
                }
            ))
            
            # Connect to remediation
            if remediation:
                self._add_edge(GraphEdge(
                    id="edge-remediation-verification",
                    source="remediation",
                    target=ver_id,
                    type=EdgeType.VERIFIED_BY,
                    label="verified by"
                ))
            
            # Connect to evidence (test results)
            self._add_edge(GraphEdge(
                id="edge-evidence-verification",
                source=f"incident-{incident.id}",
                target=ver_id,
                type=EdgeType.TESTED_BY,
                label="tests"
            ))
        
        # 8. RAG documents
        if rag_documents:
            for i, doc in enumerate(rag_documents):
                doc_id = f"doc-{doc.get('id', i)}"
                self._add_node(GraphNode(
                    id=doc_id,
                    type="document",
                    label=doc.get("title", f"Document {i+1}"),
                    data={
                        "source": doc.get("source", ""),
                        "relevance": doc.get("relevance_score", 0),
                        "snippet": doc.get("snippet", ""),
                        "matched_terms": doc.get("matched_terms", [])
                    }
                ))
                
                # Connect to relevant hypotheses/evidence
                if doc.get("matched_terms"):
                    for hyp in hypotheses:
                        hyp_text = (hyp.title + " " + hyp.description).lower()
                        if any(term.lower() in hyp_text for term in doc["matched_terms"]):
                            self._add_edge(GraphEdge(
                                id=f"edge-{doc_id}-hypothesis-{hyp.id}",
                                source=doc_id,
                                target=f"hypothesis-{hyp.id}",
                                type=EdgeType.RELATED_TO,
                                label=f"informs ({doc.get('relevance_score', 0):.0%})"
                            ))
        
        # Generate layout positions (simple hierarchical)
        self._generate_positions()
        
        return EvidenceGraph(
            incident_id=incident.id,
            nodes=list(self.node_map.values()),
            edges=self.edges,
            metadata={
                "node_count": len(self.node_map),
                "edge_count": len(self.edges),
                "generated_at": uuid.uuid4().hex[:8]
            }
        )
    
    def _add_node(self, node: GraphNode):
        self.node_map[node.id] = node
    
    def _add_edge(self, edge: GraphEdge):
        # Only add edge if both nodes exist
        if edge.source in self.node_map and edge.target in self.node_map:
            self.edges.append(edge)
    
    def _generate_positions(self):
        """Generate simple hierarchical positions for visualization."""
        # Group nodes by type for layout
        type_order = ["incident", "service", "component", "evidence", "document", "hypothesis", "root_cause", "remediation", "verification"]
        type_y = {t: i * 150 for i, t in enumerate(type_order)}
        
        type_counts = {t: 0 for t in type_order}
        
        for node in self.node_map.values():
            node_type = node.type
            if node_type not in type_counts:
                node_type = "evidence"
            
            x = type_counts[node_type] * 200 - 400
            y = type_y.get(node_type, 0)
            
            node.position = {"x": float(x), "y": float(y)}
            type_counts[node_type] += 1
    
    def to_cytoscape_elements(self) -> List[Dict[str, Any]]:
        """Convert to Cytoscape.js elements format for frontend visualization."""
        elements = []
        
        for node in self.node_map.values():
            elements.append({
                "data": {
                    "id": node.id,
                    "label": node.label,
                    "type": node.type,
                    **node.data
                },
                "position": node.position or {"x": 0, "y": 0},
                "classes": node.type
            })
        
        for edge in self.edges:
            elements.append({
                "data": {
                    "id": edge.id,
                    "source": edge.source,
                    "target": edge.target,
                    "type": edge.type.value,
                    "weight": edge.weight,
                    "label": edge.label,
                    **edge.metadata
                },
                "classes": edge.type.value
            })
        
        return elements
    
    def to_svg(self, width: int = 800, height: int = 600) -> str:
        """Generate simple SVG representation of the graph."""
        # This is a simplified SVG generator for basic visualization
        svg_parts = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
            '<defs>',
            '<marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">',
            '<polygon points="0 0, 10 3.5, 0 7" fill="#888"/>',
            '</marker>',
            '</defs>'
        ]
        
        # Colors by node type
        type_colors = {
            "incident": "#ff4444",
            "service": "#4488ff",
            "component": "#44ff88",
            "evidence": "#ffaa44",
            "document": "#aa44ff",
            "hypothesis": "#ffff44",
            "root_cause": "#ff44ff",
            "remediation": "#44ffff",
            "verification": "#88ff88",
        }
        
        edge_colors = {
            "supports": "#44ff44",
            "contradicts": "#ff4444",
            "caused_by": "#ff8844",
            "related_to": "#8888ff",
            "derived_from": "#8844ff",
            "tested_by": "#ff88ff",
            "verified_by": "#44ffff",
        }
        
        # Draw edges first (behind nodes)
        for edge in self.edges:
            source = self.node_map.get(edge.source)
            target = self.node_map.get(edge.target)
            if not source or not target or not source.position or not target.position:
                continue
            
            x1, y1 = source.position["x"] + width/2, source.position["y"] + height/2
            x2, y2 = target.position["x"] + width/2, target.position["y"] + height/2
            
            color = edge_colors.get(edge.type.value, "#888")
            svg_parts.append(
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'stroke="{color}" stroke-width="{edge.weight * 2}" '
                f'marker-end="url(#arrowhead)"/>'
            )
            
            # Edge label
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            if edge.label:
                svg_parts.append(
                    f'<text x="{mx}" y="{my - 5}" font-size="10" fill="{color}" text-anchor="middle">'
                    f'{edge.label}</text>'
                )
        
        # Draw nodes
        for node in self.node_map.values():
            if not node.position:
                continue
            x, y = node.position["x"] + width/2, node.position["y"] + height/2
            color = type_colors.get(node.type, "#888")
            
            svg_parts.append(
                f'<circle cx="{x}" cy="{y}" r="30" fill="{color}" stroke="#fff" stroke-width="2"/>'
            )
            svg_parts.append(
                f'<text x="{x}" y="{y + 5}" font-size="11" fill="#fff" text-anchor="middle" font-weight="bold">'
                f'{node.label}</text>'
            )
        
        svg_parts.append('</svg>')
        return "\n".join(svg_parts)


def build_evidence_graph(
    incident: Incident,
    evidence: List[Evidence],
    hypotheses: List[Hypothesis],
    root_cause: Optional[Dict[str, Any]] = None,
    remediation: Optional[Dict[str, Any]] = None,
    verification: Optional[Dict[str, Any]] = None,
    rag_documents: Optional[List[Dict[str, Any]]] = None
) -> EvidenceGraph:
    """Convenience function to build evidence graph."""
    builder = EvidenceGraphBuilder()
    return builder.build(
        incident, evidence, hypotheses, root_cause, remediation, verification, rag_documents
    )