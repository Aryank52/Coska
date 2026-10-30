import { useState, useEffect, useRef } from 'react'
import { getServiceMap, getServiceStatusOverview, getBlastRadius, updateServiceStatus } from '../services/api'
import type { ServiceMap as ServiceMapType, BlastRadius } from '../types/incident'
import { Server, Database, Globe, Network, Cpu, Target, Share2, RotateCcw } from 'lucide-react'

const SERVICE_TYPE_CONFIG: Record<string, { color: string; icon: any; label: string; shape: string }> = {
  client: { color: '#8888ff', icon: Server, label: 'Client', shape: 'rectangle' },
  gateway: { color: '#ff8844', icon: Share2, label: 'Gateway', shape: 'diamond' },
  api: { color: '#4488ff', icon: Server, label: 'API', shape: 'ellipse' },
  database: { color: '#44ff88', icon: Database, label: 'Database', shape: 'hexagon' },
  cache: { color: '#ffaa44', icon: Cpu, label: 'Cache', shape: 'octagon' },
  queue: { color: '#aa44ff', icon: Network, label: 'Queue', shape: 'vee' },
  external: { color: '#ff44ff', icon: Globe, label: 'External', shape: 'star' },
}

const STATUS_COLORS = {
  healthy: '#44ff44',
  degraded: '#ffaa44',
  critical: '#ff4444',
  unknown: '#888888',
}

const DEPENDENCY_COLORS = {
  critical: '#ff4444',
  degraded: '#ffaa44',
  optional: '#44ff44',
}

export function ServiceMap() {
  const [serviceMap, setServiceMap] = useState<ServiceMapType | null>(null)
  const [statusOverview, setStatusOverview] = useState<any>(null)
  const [selectedService, setSelectedService] = useState<string | null>(null)
  const [blastRadius, setBlastRadius] = useState<BlastRadius | null>(null)
  const [loading, setLoading] = useState(true)
  const [blastLoading, setBlastLoading] = useState(false)

  useEffect(() => {
    loadServiceMap()
    loadStatusOverview()
  }, [])

  const loadServiceMap = async () => {
    try {
      const data = await getServiceMap()
      setServiceMap(data)
    } catch (error) {
      console.error('Failed to load service map:', error)
    }
  }

  const loadStatusOverview = async () => {
    try {
      const data = await getServiceStatusOverview()
      setStatusOverview(data)
    } catch (error) {
      console.error('Failed to load status overview:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleServiceClick = async (serviceId: string) => {
    setSelectedService(serviceId)
    setBlastLoading(true)
    try {
      const radius = await getBlastRadius(serviceId)
      setBlastRadius(radius)
    } catch (error) {
      console.error('Failed to load blast radius:', error)
    } finally {
      setBlastLoading(false)
    }
  }

  const handleStatusChange = async (serviceId: string, status: string) => {
    await updateServiceStatus(serviceId, status)
    loadStatusOverview()
    if (serviceMap) {
      const updated = { ...serviceMap }
      const service = updated.services.find(s => s.id === serviceId)
      if (service) service.status = status as any
      setServiceMap(updated)
    }
  }

  if (loading) return <div className="card" style={{ padding: 48, textAlign: 'center' }}>Loading service map...</div>

  if (!serviceMap) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 48 }}>
        <Network style={{ width: 48, height: 48, color: 'var(--fg-muted)', marginBottom: 16 }} />
        <h3>Service map not available</h3>
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h2 className="page-title">Service Map</h2>
          <p className="page-subtitle">Service dependency topology and blast radius analysis</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-primary" onClick={loadStatusOverview} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <RotateCcw style={{ width: 16, height: 16 }} />
            Refresh Status
          </button>
        </div>
      </div>

      {/* Status Overview */}
      {statusOverview && (
        <div className="card" style={{ marginBottom: 24, padding: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <Target style={{ width: 18, height: 18, color: 'var(--accent-primary)' }} />
            <span style={{ fontSize: 13, fontWeight: 600, textTransform: 'uppercase' }}>System Health</span>
          </div>
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#44ff44' }} />
              <span>Healthy: {statusOverview.healthy}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#ffaa44' }} />
              <span>Degraded: {statusOverview.degraded}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#ff4444' }} />
              <span>Critical: {statusOverview.critical}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#888888' }} />
              <span>Unknown: {statusOverview.unknown}</span>
            </div>
          </div>
        </div>
      )}

      {/* Main Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 24 }}>
        {/* Service Map Canvas */}
        <div className="card" style={{ minHeight: 600, position: 'relative' }}>
          <div style={{ padding: 16, borderBottom: '1px solid var(--border-primary)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 13, fontWeight: 600, textTransform: 'uppercase' }}>Topology</span>
              {selectedService && (
                <button onClick={() => setSelectedService(null)} className="btn btn-ghost" style={{ fontSize: 11, padding: '4px 8px' }}>
                  Clear Selection
                </button>
              )}
            </div>
          </div>
          <div style={{ height: 520, position: 'relative' }}>
            <ServiceMapCanvas 
              serviceMap={serviceMap}
              selectedService={selectedService}
              onServiceClick={handleServiceClick}
            />
          </div>
        </div>

        {/* Side Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Selected Service Details */}
          {selectedService && (
            <ServiceDetailPanel
              serviceMap={serviceMap}
              selectedServiceId={selectedService}
              blastRadius={blastRadius}
              blastLoading={blastLoading}
              onStatusChange={handleStatusChange}
              onClose={() => setSelectedService(null)}
              onServiceClick={handleServiceClick}
            />
          )}

          {/* All Services List */}
          <ServiceListPanel
            serviceMap={serviceMap}
            onSelect={handleServiceClick}
            selectedService={selectedService}
          />
        </div>
      </div>

      {/* Blast Radius Detail */}
      {blastRadius && (
        <div className="card" style={{ marginTop: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Target style={{ width: 20, height: 20, color: 'var(--accent-danger)' }} />
            <div className="section-title" style={{ margin: 0 }}>Blast Radius Analysis</div>
            <span className="badge" style={{ background: 'var(--accent-danger)20', color: 'var(--accent-danger)' }}>
              {blastRadius.severity}
            </span>
          </div>
          
          <div className="grid grid-4" style={{ marginBottom: 16 }}>
            <div className="card">
              <div className="stat-label">Direct Dependencies</div>
              <div className="stat-value">{blastRadius.direct_dependencies.length}</div>
            </div>
            <div className="card">
              <div className="stat-label">Transitive Dependencies</div>
              <div className="stat-value">{blastRadius.transitive_dependencies.length}</div>
            </div>
            <div className="card">
              <div className="stat-label">Impacted Services</div>
              <div className="stat-value">{blastRadius.impacted_services.length}</div>
            </div>
            <div className="card">
              <div className="stat-label">Error Increase</div>
              <div className="stat-value" style={{ color: 'var(--accent-danger)' }}>{blastRadius.error_increase_percent.toFixed(0)}%</div>
            </div>
          </div>

          {blastRadius.impacted_services.length > 0 && (
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12 }}>Impacted Services</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {blastRadius.impacted_services.map((impact: any) => (
                  <div key={impact.service_id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-primary)' }}>
                    <span style={{ width: 24, height: 24, borderRadius: '50%', background: DEPENDENCY_COLORS[impact.impact_level.toLowerCase() as keyof typeof DEPENDENCY_COLORS] || '#888', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 10, fontWeight: 600 }}>
                      {impact.impact_level.charAt(0)}
                    </span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 13, fontWeight: 600 }}>{impact.service_name}</div>
                      <div style={{ fontSize: 11, color: 'var(--fg-muted)' }}>{impact.path}</div>
                    </div>
                    <span className="badge" style={{ background: DEPENDENCY_COLORS[impact.dependency_type as keyof typeof DEPENDENCY_COLORS] + '20', color: DEPENDENCY_COLORS[impact.dependency_type as keyof typeof DEPENDENCY_COLORS] }}>
                      {impact.dependency_type}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function ServiceMapCanvas({ serviceMap, selectedService, onServiceClick }: { 
  serviceMap: ServiceMapType; 
  selectedService: string | null;
  onServiceClick: (id: string) => any;
  statusOverview?: any;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  
  useEffect(() => {
    if (!canvasRef.current) return
    drawCanvas()
  }, [serviceMap, selectedService])

  const drawCanvas = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    
    const width = canvas.width
    const height = canvas.height
    
    ctx.clearRect(0, 0, width, height)
    
    // Draw edges first
    for (const edge of serviceMap.dependencies) {
      const source = serviceMap.services.find(s => s.id === edge.source)
      const target = serviceMap.services.find(s => s.id === edge.target)
      if (!source?.position || !target?.position) continue
      
      const x1 = source.position.x
      const y1 = source.position.y
      const x2 = target.position.x
      const y2 = target.position.y
      
      const depColor = DEPENDENCY_COLORS[edge.type] || '#888'
      
      ctx.beginPath()
      ctx.moveTo(x1, y1)
      ctx.lineTo(x2, y2)
      ctx.strokeStyle = depColor
      ctx.lineWidth = edge.type === 'critical' ? 3 : (edge.type === 'degraded' ? 2 : 1)
      ctx.stroke()
      
      // Arrow
      const angle = Math.atan2(y2 - y1, x2 - x1)
      const headLen = 8
      ctx.beginPath()
      ctx.moveTo(x2, y2)
      ctx.lineTo(x2 - headLen * Math.cos(angle - Math.PI / 6), y2 - headLen * Math.sin(angle - Math.PI / 6))
      ctx.moveTo(x2, y2)
      ctx.lineTo(x2 - headLen * Math.cos(angle + Math.PI / 6), y2 - headLen * Math.sin(angle + Math.PI / 6))
      ctx.strokeStyle = depColor
      ctx.stroke()
    }
    
    // Draw nodes
    for (const service of serviceMap.services) {
      if (!service.position) continue
      
      const x = service.position.x
      const y = service.position.y
      const isSelected = selectedService === service.id
      
      const typeConfig = SERVICE_TYPE_CONFIG[service.type] || { color: '#888', shape: 'ellipse' }
      const statusColor = STATUS_COLORS[service.status] || '#888'
      
      // Node background
      ctx.beginPath()
      if (typeConfig.shape === 'rectangle') {
        ctx.rect(x - 50, y - 25, 100, 50)
      } else if (typeConfig.shape === 'diamond') {
        ctx.moveTo(x, y - 30)
        ctx.lineTo(x + 40, y)
        ctx.lineTo(x, y + 30)
        ctx.lineTo(x - 40, y)
        ctx.closePath()
      } else if (typeConfig.shape === 'hexagon') {
        for (let i = 0; i < 6; i++) {
          const angle = (Math.PI / 3) * i - Math.PI / 6
          const px = x + 35 * Math.cos(angle)
          const py = y + 35 * Math.sin(angle)
          if (i === 0) ctx.moveTo(px, py)
          else ctx.lineTo(px, py)
        }
        ctx.closePath()
      } else {
        ctx.arc(x, y, 30, 0, Math.PI * 2)
      }
      
      ctx.fillStyle = typeConfig.color
      ctx.fill()
      
      // Status ring
      ctx.strokeStyle = statusColor
      ctx.lineWidth = isSelected ? 4 : 2
      ctx.stroke()
      
      if (isSelected) {
        ctx.strokeStyle = '#fff'
        ctx.lineWidth = 2
        ctx.stroke()
      }
      
      // Label
      ctx.fillStyle = '#fff'
      ctx.font = 'bold 11px monospace'
      ctx.textAlign = 'center'
      ctx.fillText(service.name, x, y + 4)
    }
  }
  
  return (
    <canvas
      ref={canvasRef}
      width={800}
      height={520}
      style={{ width: '100%', height: '100%', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)', cursor: 'crosshair' }}
      onClick={(e) => {
        const canvas = canvasRef.current
        if (!canvas) return
        const rect = canvas.getBoundingClientRect()
        const scaleX = canvas.width / rect.width
        const scaleY = canvas.height / rect.height
        const clickX = (e.clientX - rect.left) * scaleX
        const clickY = (e.clientY - rect.top) * scaleY
        
        for (const service of serviceMap.services) {
          if (!service.position) continue
          const dx = clickX - service.position.x
          const dy = clickY - service.position.y
          if (dx * dx + dy * dy <= 35 * 35) {
            onServiceClick(service.id)
            break
          }
        }
      }}
    />
  )
}

function ServiceDetailPanel({ serviceMap, selectedServiceId, blastRadius, blastLoading, onStatusChange, onClose, onServiceClick }: {
  serviceMap: ServiceMapType;
  selectedServiceId: string;
  blastRadius: BlastRadius | null;
  blastLoading: boolean;
  onStatusChange: (id: string, status: string) => void;
  onClose: () => void;
  onServiceClick: (id: string) => void;
}) {
  const service = serviceMap.services.find(s => s.id === selectedServiceId)
  if (!service) return null
  
  const typeConfig = SERVICE_TYPE_CONFIG[service.type] || { color: '#888', icon: null, label: 'Service' }
  const Icon = typeConfig.icon
  const statusColor = STATUS_COLORS[service.status] || '#888'
  const dependents = serviceMap.services.filter(s => 
    serviceMap.dependencies.some(e => e.source === s.id && e.target === selectedServiceId)
  )
  const dependencies = serviceMap.services.filter(s => 
    serviceMap.dependencies.some(e => e.source === selectedServiceId && e.target === s.id)
  )
  
  return (
    <div className="card" style={{ borderColor: typeConfig.color }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 'var(--radius-md)', background: typeConfig.color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Icon style={{ width: 20, height: 20, color: '#fff' }} />
          </div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 600 }}>{service.name}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
              <span className="badge badge-low">{typeConfig.label}</span>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: statusColor }} />
              <span style={{ fontSize: 12, fontWeight: 600, color: statusColor, textTransform: 'uppercase' }}>{service.status}</span>
            </div>
          </div>
        </div>
        <button onClick={onClose} className="btn btn-ghost" style={{ padding: 4 }}>✕</button>
      </div>
      
      {service.metadata.description && (
        <div style={{ fontSize: 12, color: 'var(--fg-secondary)', marginBottom: 16, padding: 12, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
          {service.metadata.description}
        </div>
      )}
      
      {/* Quick Actions */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        <select 
          value={service.status} 
          onChange={e => onStatusChange(service.id, e.target.value)}
          className="input"
          style={{ width: 140, padding: '6px 10px', fontSize: 12 }}
        >
          <option value="healthy">Healthy</option>
          <option value="degraded">Degraded</option>
          <option value="critical">Critical</option>
          <option value="unknown">Unknown</option>
        </select>
        <button 
          onClick={() => onServiceClick(service.id)}
          className="btn btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', fontSize: 12 }}
          disabled={blastLoading}
        >
          <Target style={{ width: 14, height: 14 }} />
          Blast Radius {blastRadius ? `(${blastRadius.impacted_services.length})` : ''}
        </button>
      </div>
      
      {/* Dependencies */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--fg-muted)', marginBottom: 8, textTransform: 'uppercase' }}>Depends On ({dependencies.length})</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {dependencies.map(dep => (
            <span key={dep.id} className="badge badge-low" style={{ fontSize: 10 }}>{dep.name}</span>
          ))}
          {dependencies.length === 0 && <span style={{ fontSize: 11, color: 'var(--fg-muted)' }}>None</span>}
        </div>
      </div>
      
      {/* Dependents */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--fg-muted)', marginBottom: 8, textTransform: 'uppercase' }}>Dependents ({dependents.length})</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {dependents.map(dep => (
            <span key={dep.id} className="badge" style={{ background: 'var(--accent-info)20', color: 'var(--accent-info)', fontSize: 10 }}>{dep.name}</span>
          ))}
          {dependents.length === 0 && <span style={{ fontSize: 11, color: 'var(--fg-muted)' }}>None (leaf service)</span>}
        </div>
      </div>
      
      {/* SLOs */}
      {Object.keys(service.metadata).some(k => k.includes('slo')) && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--fg-muted)', marginBottom: 8, textTransform: 'uppercase' }}>SLOs</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8, fontSize: 11 }}>
            {Object.entries(service.metadata).filter(([k]) => k.includes('slo')).map(([k, v]) => (
              <div key={k} style={{ padding: '6px 8px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
                <div className="mono" style={{ color: 'var(--fg-muted)' }}>{k}</div>
                <div style={{ fontWeight: 600 }}>{v}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ServiceListPanel({ serviceMap, onSelect, selectedService }: {
  serviceMap: ServiceMapType;
  onSelect: (id: string) => void;
  selectedService: string | null;
}) {
  const servicesByType = serviceMap.services.reduce((acc, s) => {
    acc[s.type] = acc[s.type] || []
    acc[s.type].push(s)
    return acc
  }, {} as Record<string, typeof serviceMap.services>)
  
  const typeOrder = ['client', 'gateway', 'api', 'database', 'cache', 'queue', 'external']
  
  return (
    <div className="card" style={{ maxHeight: 600, overflow: 'auto' }}>
      <div style={{ padding: 16, borderBottom: '1px solid var(--border-primary)' }}>
        <div style={{ fontSize: 13, fontWeight: 600, textTransform: 'uppercase', color: 'var(--fg-muted)' }}>All Services</div>
      </div>
      <div style={{ padding: 8 }}>
        {typeOrder.map(type => {
          const services = servicesByType[type] || []
          if (services.length === 0) return null
          const config = SERVICE_TYPE_CONFIG[type] || { color: '#888', icon: null, label: type }
          const Icon = config.icon
          
          return (
            <div key={type} style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, padding: '0 8px' }}>
                <Icon style={{ width: 14, height: 14, color: config.color }} />
                <span style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', color: 'var(--fg-muted)' }}>{config.label}s</span>
                <span className="badge badge-low">{services.length}</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {services.map(service => {
                  const statusColor = STATUS_COLORS[service.status] || '#888'
                  const isSelected = selectedService === service.id
                  
                  return (
                    <button
                      key={service.id}
                      onClick={() => onSelect(service.id)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        padding: '8px 12px',
                        background: isSelected ? 'var(--accent-primary)15' : 'transparent',
                        border: isSelected ? '1px solid var(--accent-primary)' : '1px solid transparent',
                        borderRadius: 'var(--radius-sm)',
                        color: 'var(--fg-primary)',
                        fontSize: 12,
                        width: '100%',
                        textAlign: 'left',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                    >
                      <div style={{ width: 8, height: 8, borderRadius: '50%', background: statusColor }} />
                      <span style={{ flex: 1, fontFamily: 'var(--font-mono)', fontWeight: 500 }}>{service.name}</span>
                      <span style={{ fontSize: 10, color: 'var(--fg-muted)' }}>{service.status}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}