import { useState, useEffect } from 'react'
import { searchKnowledgeBase, listKnowledgeDocuments, listKnowledgeCategories } from '../services/api'
import type { RAGDocument, RAGSearchResult } from '../types/incident'
import { BookOpen, Search, Tag, FileText, ChevronRight, Copy } from 'lucide-react'

export function KnowledgeBase() {
  const [documents, setDocuments] = useState<RAGDocument[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<RAGSearchResult | null>(null)
  const [selectedDoc, setSelectedDoc] = useState<RAGDocument | null>(null)
  const [searchLoading, setSearchLoading] = useState(false)
  const [viewMode, setViewMode] = useState<'list' | 'search'>('list')

  useEffect(() => {
    loadDocuments()
    loadCategories()
  }, [])

  const loadDocuments = async () => {
    try {
      const data = await listKnowledgeDocuments()
      setDocuments(data.documents)
    } catch (error) {
      console.error('Failed to load documents:', error)
    }
  }

  const loadCategories = async () => {
    try {
      const data = await listKnowledgeCategories()
      setCategories(data.categories)
    } catch (error) {
      console.error('Failed to load categories:', error)
    }
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    
    setSearchLoading(true)
    try {
      const result = await searchKnowledgeBase({ query: searchQuery, top_k: 10, include_trace: true })
      setSearchResults(result)
      setViewMode('search')
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setSearchLoading(false)
    }
  }

  const filteredDocs = selectedCategory === 'all' 
    ? documents 
    : documents.filter(d => d.category === selectedCategory)

  const openDoc = async (doc: RAGDocument) => {
    setSelectedDoc(doc)
  }

  const closeDoc = () => {
    setSelectedDoc(null)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h2 className="page-title">Knowledge Base</h2>
          <p className="page-subtitle">Offline runbooks, postmortems, and engineering references</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <span className="badge badge-low">{documents.length} documents</span>
          <span className="badge badge-low">{categories.length} categories</span>
        </div>
      </div>

      {/* Search Bar */}
      <div className="card" style={{ marginBottom: 24, padding: 20 }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 200 }}>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search runbooks... (e.g., 'pool exhaustion', 'retry storm', 'cache stampede')"
              className="input"
              style={{ width: '100%' }}
            />
          </div>
          <button 
            type="submit" 
            disabled={searchLoading || !searchQuery.trim()}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <Search style={{ width: 16, height: 16 }} />
            <span>{searchLoading ? 'Searching...' : 'Search'}</span>
          </button>
        </form>
        {searchResults && (
          <div style={{ marginTop: 12, fontSize: 12, color: 'var(--fg-muted)' }}>
            Found {searchResults.documents.length} results for "{searchResults.query}" 
            (tokens: {searchResults.query_tokens.join(', ')})
          </div>
        )}
      </div>

      {/* Category Filter */}
      <div className="card" style={{ marginBottom: 24, padding: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <Tag style={{ width: 16, height: 16, color: 'var(--fg-muted)' }} />
          <span style={{ fontSize: 13, fontWeight: 600, textTransform: 'uppercase' }}>Categories</span>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          <button
            onClick={() => setSelectedCategory('all')}
            className={`btn ${selectedCategory === 'all' ? 'btn-primary' : 'btn-ghost'}`}
            style={{ padding: '6px 12px', fontSize: 12 }}
          >
            All
          </button>
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`btn ${selectedCategory === cat ? 'btn-primary' : 'btn-ghost'}`}
              style={{ padding: '6px 12px', fontSize: 12, textTransform: 'capitalize' }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {viewMode === 'search' && searchResults ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h3 style={{ fontSize: 14, fontWeight: 600 }}>Search Results</h3>
            <button onClick={() => { setViewMode('list'); setSearchResults(null); setSearchQuery(''); }} className="btn btn-ghost" style={{ fontSize: 12 }}>
              Clear Search
            </button>
          </div>
          {searchResults.documents.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: 48 }}>
              <Search style={{ width: 48, height: 48, color: 'var(--fg-muted)', marginBottom: 16 }} />
              <h3>No results found</h3>
              <p style={{ color: 'var(--fg-secondary)', marginTop: 8 }}>
                Try different keywords or browse by category.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {searchResults.documents.map((doc, i) => (
                <SearchResultCard key={doc.id} doc={doc} rank={i + 1} onClick={openDoc} trace={searchResults.trace} />
              ))}
            </div>
          )}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {filteredDocs.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: 48 }}>
              <BookOpen style={{ width: 48, height: 48, color: 'var(--fg-muted)', marginBottom: 16 }} />
              <h3>No documents in this category</h3>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {filteredDocs.map(doc => (
                <DocumentCard key={doc.id} doc={doc} onClick={openDoc} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Document Detail Modal */}
      {selectedDoc && (
        <div className="modal-overlay" onClick={closeDoc}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
              <h3 style={{ fontSize: 18, fontWeight: 600 }}>{selectedDoc.title}</h3>
              <button onClick={closeDoc} className="btn btn-ghost" style={{ padding: 4 }}>
                ✕
              </button>
            </div>
            
            <div style={{ display: 'flex', gap: 16, marginBottom: 16, flexWrap: 'wrap' }}>
              <span className="badge" style={{ background: 'var(--accent-primary)20', color: 'var(--accent-primary)' }}>
                {selectedDoc.category}
              </span>
              <span className="badge badge-low">Relevance: {(selectedDoc.relevance_score * 100).toFixed(0)}%</span>
              {selectedDoc.matched_terms.length > 0 && (
                <span className="badge" style={{ background: 'var(--accent-info)20', color: 'var(--accent-info)' }}>
                  Matched: {selectedDoc.matched_terms.join(', ')}
                </span>
              )}
            </div>

            <div style={{ marginBottom: 16, fontSize: 13, color: 'var(--fg-secondary)' }}>
              <strong>Source:</strong> {selectedDoc.source}
            </div>

            <div style={{ marginBottom: 16, fontSize: 13, color: 'var(--fg-secondary)' }}>
              <strong>Summary:</strong> {selectedDoc.summary}
            </div>

            {selectedDoc.match_reason && (
              <div style={{ marginBottom: 16, padding: 12, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', fontSize: 12, color: 'var(--accent-info)', border: '1px solid var(--border-primary)' }}>
                <strong>Why this document:</strong> {selectedDoc.match_reason}
              </div>
            )}

            <div style={{ marginBottom: 16 }}>
              <strong style={{ fontSize: 12 }}>Snippet:</strong>
              <div style={{ 
                marginTop: 8, 
                padding: 12, 
                background: 'var(--bg-tertiary)', 
                borderRadius: 'var(--radius-sm)', 
                fontSize: 13, 
                color: 'var(--fg-primary)',
                border: '1px solid var(--border-primary)',
                fontFamily: 'var(--font-mono)',
                whiteSpace: 'pre-wrap'
              }}>
                {selectedDoc.snippet}
              </div>
            </div>

            <div style={{ marginBottom: 16 }}>
              <strong style={{ fontSize: 12 }}>Tags:</strong>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
                {selectedDoc.tags.map(tag => (
                  <span key={tag} className="badge badge-low" style={{ fontSize: 11 }}>{tag}</span>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={() => copyToClipboard(JSON.stringify(selectedDoc, null, 2))} className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Copy style={{ width: 14, height: 14 }} />
                Copy JSON
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function DocumentCard({ doc, onClick }: { doc: RAGDocument; onClick: (doc: RAGDocument) => void }) {
  return (
    <div className="card" onClick={() => onClick(doc)} style={{ cursor: 'pointer', transition: 'border-color 0.2s', border: '1px solid var(--border-primary)' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
        <div style={{ width: 48, height: 48, borderRadius: 'var(--radius-md)', background: 'var(--accent-primary)15', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <FileText style={{ width: 24, height: 24, color: 'var(--accent-primary)' }} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span style={{ fontSize: 14, fontWeight: 600 }}>{doc.title}</span>
            <span className="badge badge-low">{doc.category}</span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--fg-secondary)', marginBottom: 8 }}>{doc.summary}</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {doc.tags.slice(0, 5).map(tag => (
              <span key={tag} className="badge badge-low" style={{ fontSize: 10 }}>{tag}</span>
            ))}
            {doc.tags.length > 5 && (
              <span className="badge badge-low" style={{ fontSize: 10 }}>+{doc.tags.length - 5} more</span>
            )}
          </div>
        </div>
        <ChevronRight style={{ width: 20, height: 20, color: 'var(--fg-muted)', flexShrink: 0 }} />
      </div>
    </div>
  )
}

function SearchResultCard({ doc, rank, onClick, trace }: { doc: RAGDocument; rank: number; onClick: (doc: RAGDocument) => void; trace?: any }) {
  const traceItem = trace?.top_results?.find((t: any) => t.id === doc.id)
  
  return (
    <div className="card" onClick={() => onClick(doc)} style={{ cursor: 'pointer', border: '1px solid var(--border-primary)' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
        <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--accent-primary)15', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, fontWeight: 600, color: 'var(--accent-primary)', fontFamily: 'var(--font-mono)' }}>
          #{rank}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span style={{ fontSize: 14, fontWeight: 600 }}>{doc.title}</span>
            <span className="badge" style={{ background: 'var(--accent-primary)20', color: 'var(--accent-primary)' }}>
              {(doc.relevance_score * 100).toFixed(0)}%
            </span>
            <span className="badge badge-low">{doc.category}</span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--fg-secondary)', marginBottom: 8 }}>{doc.snippet}</div>
          
          {traceItem && (
            <div style={{ fontSize: 11, color: 'var(--accent-info)', marginBottom: 8, fontFamily: 'var(--font-mono)' }}>
              {traceItem.match_reason}
            </div>
          )}
          
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {doc.tags.slice(0, 5).map(tag => (
              <span key={tag} className="badge badge-low" style={{ fontSize: 10 }}>{tag}</span>
            ))}
          </div>
        </div>
        <ChevronRight style={{ width: 20, height: 20, color: 'var(--fg-muted)', flexShrink: 0 }} />
      </div>
    </div>
  )
}