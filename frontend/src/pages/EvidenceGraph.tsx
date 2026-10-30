import { useParams } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'
import { getEvidenceGraph } from '../services/api'
import type { EvidenceGraph } from '../types/incident'
import { Target, FileText, Lightbulb, Shield, CheckCircle, Network, Database, Server, Globe } from 'lucide-react'

const NODE_TYPE_CONFIG: Record<string, { color: string; icon: any; label: string }> = {
  incident: { color: '#ff4444', icon: Target, label: 'Incident' },
  service: { color: '#4488ff', icon: Server, label: 'Service' },
  component: { color: '#44ff88', icon: Database, label: 'Component' },
  evidence: { color: '#ffaa44', icon: FileText, label: 'Evidence' },
  document: { color: '#aa44ff', icon: Globe, label: 'Document' },
  hypothesis: { color: '#ffff44', icon: Lightbulb, label: 'Hypothesis' },
  root_cause: { color: '#ff44ff', icon: Target, label: 'Root Cause' },
  remediation: { color: '#44ffff', icon: Shield, label: 'Remediation' },
  verification: { color: '#88ff88', icon: CheckCircle, label: 'Verification' },
}

const EDGE_TYPE_CONFIG: Record<string, { color: string; label: string }> = {
  supports: { color: '#44ff44', label: 'Supports' },
  contradicts: { color: '#ff4444', label: 'Contradicts' },
  caused_by: { color: '#ff8844', label: 'Caused By' },
  related_to: { color: '#8888ff', label: 'Related' },
  derived_from: { color: '#8844ff', label: 'Derived From' },
  tested_by: { color: '#ff88ff', label: 'Tested By' },
  verified_by: { color: '#44ffff', label: 'Verified By' },
}

export function EvidenceGraph() {
  const { id } = useParams<{ id: string }>()
  const [graph, setGraph] = useState<EvidenceGraph | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedNode, setSelectedNode] = useState<any>(null)
  const [layout, setLayout] = useState<'hierarchical' | 'force' | 'radial'>('hierarchical')
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    if (!id) return
    loadGraph()
  }, [id])

  const loadGraph = async () => {
    try {
      const data = await getEvidenceGraph(id!)
      setGraph(data)
    } catch (error) {
      console.error('Failed to load evidence graph:', error)
    } finally {
      setLoading(false)
    }
  }

  // Simple canvas-based graph rendering
  const drawGraph = () => {
    const canvas = canvasRef.current
    if (!canvas || !graph) return
    
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    
    const width = canvas.width
    const height = canvas.height
    
    ctx.clearRect(0, 0, width, height)
    
    // Draw edges first
    for (const edge of graph.edges) {
      const source = graph.nodes.find(n => n.id === edge.source)
      const target = graph.nodes.find(n => n.id === edge.target)
      if (!source?.position || !target?.position) continue
      
      const x1 = source.position.x + width / 2
      const y1 = source.position.y + height / 2
      const x2 = target.position.x + width / 2
      const y2 = target.position.y + height / 2
      
      const edgeConfig = EDGE_TYPE_CONFIG[edge.type] || { color: '#888', label: edge.type }
      
      ctx.beginPath()
      ctx.moveTo(x1, y1)
      ctx.lineTo(x2, y2)
      ctx.strokeStyle = edgeConfig.color
      ctx.lineWidth = Math.max(1, edge.weight * 2)
      ctx.stroke()
      
      // Arrow head
      const angle = Math.atan2(y2 - y1, x2 - x1)
      const headLen = 10
      ctx.beginPath()
      ctx.moveTo(x2, y2)
      ctx.lineTo(x2 - headLen * Math.cos(angle - Math.PI / 6), y2 - headLen * Math.sin(angle - Math.PI / 6))
      ctx.moveTo(x2, y2)
      ctx.lineTo(x2 - headLen * Math.cos(angle + Math.PI / 6), y2 - headLen * Math.sin(angle + Math.PI / 6))
      ctx.strokeStyle = edgeConfig.color
      ctx.stroke()
    }
    
    // Draw nodes
    for (const node of graph.nodes) {
      if (!node.position) continue
      
      const x = node.position.x + width / 2
      const y = node.position.y + height / 2
      
      const config = NODE_TYPE_CONFIG[node.type] || { color: '#888', icon: null, label: node.type }
      const isSelected = selectedNode?.id === node.id
      
      // Node circle
      ctx.beginPath()
      ctx.arc(x, y, isSelected ? 35 : 30, 0, Math.PI * 2)
      ctx.fillStyle = config.color
      ctx.fill()
      
      if (isSelected) {
        ctx.strokeStyle = '#fff'
        ctx.lineWidth = 3
        ctx.stroke()
      }
      
      // Node label
      ctx.fillStyle = '#fff'
      ctx.font = 'bold 11px monospace'
      ctx.textAlign = 'center'
      ctx.fillText(node.label, x, y + 4)
    }
  }

  useEffect(() => {
    if (graph && canvasRef.current) {
      drawGraph()
    }
  }, [graph, selectedNode])

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!graph) return
    
    const rect = canvasRef.current!.getBoundingClientRect()
    const x = e.clientX - rect.left - canvasRef.current!.width / 2
    const y = e.clientY - rect.top - canvasRef.current!.height / 2
    
    // Find clicked node
    for (const node of graph.nodes) {
      if (!node.position) continue
      const dx = node.position.x - x
      const dy = node.position.y - y
      if (dx * dx + dy * dy < 35 * 35) {
        setSelectedNode(node)
        return
      }
    }
    setSelectedNode(null)
  }

  if (loading) return <div className="card" style={{ padding: 48, textAlign: 'center' }}>Loading evidence graph...</div>

  if (!graph) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 48 }}>
        <Network style={{ width: 48, height: 48, color: 'var(--fg-muted)', marginBottom: 16 }} />
        <h3>Evidence graph not available</h3>
        <p style={{ color: 'var(--fg-secondary)', marginTop: 8 }}>
          The evidence graph will appear here once the investigation has collected evidence and generated hypotheses.
        </p>
      </div>
    )
  }

  const nodeTypeCounts = graph.nodes.reduce((acc, n) => {
    acc[n.type] = (acc[n.type] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h2 className="page-title">Evidence Graph</h2>
          <p className="page-subtitle">Relationships between incident, evidence, hypotheses, and conclusions</p>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <select value={layout} onChange={e => setLayout(e.target.value as any)} className="input" style={{ width: 140, padding: '8px 12px' }}>
            <option value="hierarchical">Hierarchical</option>
            <option value="force">Force Directed</option>
            <option value="radial">Radial</option>
          </select>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-4" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="stat-label">Nodes</div>
          <div className="stat-value" style={{ color: 'var(--accent-primary)' }}>{graph.nodes.length}</div>
        </div>
        <div className="card">
          <div className="stat-label">Edges</div>
          <div className="stat-value" style={{ color: 'var(--accent-info)' }}>{graph.edges.length}</div>
        </div>
        <div className="card">
          <div className="stat-label">Types</div>
          <div className="stat-value" style={{ color: 'var(--accent-warning)' }}>{Object.keys(nodeTypeCounts).length}</div>
        </div>
        <div className="card">
          <div className="stat-label">Layout</div>
          <div className="stat-value" style={{ color: 'var(--accent-secondary)' }}>{layout}</div>
        </div>
      </div>

      {/* Canvas */}
      <div className="card" style={{ position: 'relative', minHeight: 500 }}>
        <canvas
          ref={canvasRef}
          width={800}
          height={500}
          style={{ width: '100%', height: '100%', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}
          onClick={handleCanvasClick}
        />
        {selectedNode && (
          <div style={{ position: 'absolute', bottom: 20, left: 20, right: 20, background: 'var(--bg-elevated)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-md)', padding: 16, zIndex: 10, boxShadow: '0 -4px 20px rgba(0,0,0,0.3)' }}>
            <NodeDetailPanel node={selectedNode} graph={graph} onClose={() => setSelectedNode(null)} />
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="card" style={{ marginTop: 16 }}>
        <div className="section-title">Legend</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, marginTop: 12 }}>
          {Object.entries(NODE_TYPE_CONFIG).map(([type, config]) => {
            if (!nodeTypeCounts[type]) return null
            return (
              <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ width: 16, height: 16, borderRadius: '50%', background: config.color }} />
                <span style={{ fontSize: 12 }}>{config.label} ({nodeTypeCounts[type]})</span>
              </div>
            )
          })}
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, marginTop: 12 }}>
          {Object.entries(EDGE_TYPE_CONFIG).map(([type, config]) => {
            const count = graph.edges.filter(e => e.type === type).length
            if (!count) return null
            return (
              <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ width: 24, height: 3, background: config.color, borderRadius: 2 }} />
                <span style={{ fontSize: 12 }}>{config.label} ({count})</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Node Type Summary */}
      <div className="card" style={{ marginTop: 16 }}>
        <div className="section-title">Node Summary</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12, marginTop: 12 }}>
          {Object.entries(nodeTypeCounts).map(([type, count]) => {
            const config = NODE_TYPE_CONFIG[type] || { color: '#888', icon: null, label: type }
            const nodes = graph.nodes.filter(n => n.type === type)
            return (
              <div key={type} className="card" style={{ padding: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <div style={{ width: 12, height: 12, borderRadius: '50%', background: config.color }} />
                  <span style={{ fontSize: 13, fontWeight: 600, textTransform: 'capitalize' }}>{config.label}s</span>
                  <span className="badge badge-low">{count}</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 11, color: 'var(--fg-muted)', maxHeight: 150, overflow: 'auto' }}>
                  {nodes.slice(0, 5).map(node => (
                    <span key={node.id} className="mono">{node.label}</span>
                  ))}
                  {nodes.length > 5 && <span>... and {nodes.length - 5} more</span>}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function NodeDetailPanel({ node, graph, onClose }: { node: any; graph: EvidenceGraph; onClose: () => void }) {
  const config = NODE_TYPE_CONFIG[node.type] || { color: '#888', icon: null, label: node.type }
  const Icon = config.icon
  
  // Find connected edges
  const incomingEdges = graph.edges.filter(e => e.target === node.id)
  const outgoingEdges = graph.edges.filter(e => e.source === node.id)
  
  return (
    <div style={{ display: 'flex', gap: 16 }}>
      <button onClick={onClose} style={{ position: 'absolute', top: 8, right: 8, background: 'none', border: 'none', color: 'var(--fg-muted)', cursor: 'pointer', padding: 4 }}>✕</button>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 8, background: config.color, borderRadius: 'var(--radius-md)', color: '#fff' }}>
        <Icon style={{ width: 24, height: 24 }} />
        <div>
          <div style={{ fontSize: 14, fontWeight: 600 }}>{node.label}</div>
          <div style={{ fontSize: 11, opacity: 0.8 }}>{config.label}</div>
        </div>
      </div>
      
      <div style={{ flex: 1 }}>
        {node.data && Object.keys(node.data).length > 0 && (
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--fg-muted)', marginBottom: 8, textTransform: 'uppercase' }}>Details</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: 8, fontSize: 11 }}>
              {Object.entries(node.data).map(([key, value]) => (
                <div key={key} style={{ padding: '6px 8px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
                  <div className="mono" style={{ fontSize: 10, color: 'var(--fg-muted)' }}>{key}</div>
                  <div style={{ fontSize: 11, color: 'var(--fg-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div style={{ display: 'flex', gap: 16, fontSize: 11, color: 'var(--fg-muted)' }}>
          <span>Incoming: {incomingEdges.length}</span>
          <span>Outgoing: {outgoingEdges.length}</span>
        </div>
      </div>
    </div>
  )
}