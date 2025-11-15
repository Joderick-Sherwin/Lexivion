import { useState, useMemo } from 'react'
import { createPortal } from 'react-dom'
import { ImageIcon, FileText, X } from 'lucide-react'
import axios from 'axios'
import './ResultsDisplay.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const Modal = ({ children, onClose, contentClassName = '' }) => {
  if (typeof document === 'undefined') return null
  return createPortal(
    <div className="modal-overlay" onClick={onClose}>
      <div
        className={`modal-content ${contentClassName}`}
        onClick={(event) => event.stopPropagation()}
      >
        {children}
      </div>
    </div>,
    document.body
  )
}

function ResultsDisplay({ result }) {
  const [activeChunk, setActiveChunk] = useState(null)
  const [activeImage, setActiveImage] = useState(null)
  const chunkLookup = useMemo(() => {
    const lookup = new Map()
    result?.context?.forEach((ctx) => {
      lookup.set(ctx.chunk_id, ctx)
    })
    return lookup
  }, [result])

  if (!result) {
    return null
  }

  const decodeBase64Image = (base64) => {
    try {
      return `data:image/png;base64,${base64}`
    } catch (e) {
      return null
    }
  }

  const hasSections = result.sections && result.sections.length > 0

  const buildPdfUrl = (chunk) => {
    if (!chunk?.document?.url) return null
    const page = chunk.page_number || 1
    return `${API_URL}${chunk.document.url}#page=${page}`
  }

  const openChunkViewer = async (chunk) => {
    const token = localStorage.getItem('lexivion_token')
    const rawUrl = buildPdfUrl(chunk)
    if (!rawUrl || !token) return
    try {
      const res = await axios.get(rawUrl.replace(`#page=${chunk.page_number || 1}`, ''), {
        responseType: 'blob',
        headers: { Authorization: `Bearer ${token}` },
      })
      const blobUrl = URL.createObjectURL(res.data)
      setActiveChunk({
        title: `Chunk ${chunk.chunk_id} · Page ${chunk.page_number || 'N/A'}`,
        url: `${blobUrl}#page=${chunk.page_number || 1}`,
        filename: chunk.document?.filename,
        objectUrl: blobUrl,
      })
    } catch (e) {
      return
    }
  }

  const openImageViewer = (image) => {
    const decoded = decodeBase64Image(image.image_base64)
    if (!decoded) return
    setActiveImage({
      title: image.metadata?.filename || `Image from page ${image.page_number}`,
      description: `Page ${image.page_number} · Chunk ${image.chunk_index || image.id}`,
      src: decoded,
    })
  }

  const handleImageCardClick = (event, image) => {
    event.stopPropagation()
    openImageViewer(image)
  }

  const handleImageCardKeyDown = (event, image) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      event.stopPropagation()
      openImageViewer(image)
    }
  }

  const handleChunkButtonClick = (chunkId) => {
    const chunk = chunkLookup.get(chunkId)
    if (chunk) {
      openChunkViewer(chunk)
    }
  }

  return (
    <div className="results-section">
      <div className="section-header">
        <FileText size={24} />
        <div>
          <h2>Answer</h2>
          <p className="model-label">Model: {result.model || 'retriever_only'}</p>
        </div>
      </div>

      {result.error && (
        <div className="status-banner error compact">
          <span>{result.error}</span>
        </div>
      )}

      {result.answer && (
        <div className="final-answer">
          <h3>Gemini Response</h3>
          <p>{result.answer}</p>
        </div>
      )}

      {hasSections ? (
        <div className="results-list">
          {result.sections.map((section, index) => (
            <div key={index} className="result-card">
              <div className="result-header">
                <div>
                  <span className="result-rank">Section {index + 1}</span>
                  <h3>{section.title || 'Relevant Context'}</h3>
                </div>
                {section.chunk_ids?.length > 0 && (
                  <div className="chunk-badge">
                    {section.chunk_ids.length} chunk{section.chunk_ids.length > 1 ? 's' : ''}
                  </div>
                )}
              </div>

              {section.text && (
                <div className="result-text">
                  <p>{section.text}</p>
                </div>
              )}

              {section.chunk_ids?.length > 0 && (
                <div className="section-chunk-list">
                  {section.chunk_ids.map((chunkId) => {
                    const chunk = chunkLookup.get(chunkId)
                    const similarity =
                      typeof chunk?.metadata?.similarity === 'number'
                        ? `${(chunk.metadata.similarity * 100).toFixed(1)}% match`
                        : null
                    return (
                      <button
                        key={chunkId}
                        type="button"
                        className="chunk-card"
                        onClick={() => handleChunkButtonClick(chunkId)}
                      >
                        <div className="chunk-card-header">
                          <span>Chunk {chunkId}</span>
                          {chunk?.page_number && <span>Page {chunk.page_number}</span>}
                        </div>
                        <p>
                          {chunk?.content
                            ? `${chunk.content.slice(0, 140)}${
                                chunk.content.length > 140 ? '…' : ''
                              }`
                            : 'Preview unavailable'}
                        </p>
                        <div className="chunk-card-meta">
                          {chunk?.document?.filename && <span>{chunk.document.filename}</span>}
                          {similarity && <span>{similarity}</span>}
                        </div>
                      </button>
                    )
                  })}
                </div>
              )}

              {section.images?.length ? (
                <div className="images-grid">
                  {section.images.map((image) => (
                    <button
                      key={image.id}
                      type="button"
                      className="image-card"
                      onClick={() => openImageViewer(image)}
                      aria-label={`Open image from page ${image.page_number}`}
                    >
                      <img
                        src={decodeBase64Image(image.image_base64)}
                        alt={`Page ${image.page_number}`}
                      />
                      <div className="image-card-footer">
                        <span>
                          Page {image.page_number} · Chunk {image.chunk_index || image.id}
                        </span>
                        <span className="image-view-hint">Click to enlarge</span>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="no-image">
                  <ImageIcon size={18} />
                  <span>No associated images</span>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="no-results">
          <p>{result.error || 'No relevant context found. Try a different query.'}</p>
        </div>
      )}

      {result.context && result.context.length > 0 && (
        <div className="context-panel">
          <h3>Context Segments Used</h3>
          <div className="context-list">
            {result.context.map((ctx) => {
              const similarity =
                typeof ctx.metadata?.similarity === 'number'
                  ? (ctx.metadata.similarity * 100).toFixed(1)
                  : 'N/A'
              return (
                <button
                  key={ctx.chunk_id}
                  className="context-chip"
                  type="button"
                  onClick={() => openChunkViewer(ctx)}
                >
                  <span className="chunk-id">Chunk {ctx.chunk_id}</span>
                  {ctx.page_number !== undefined && <span>Page {ctx.page_number}</span>}
                  <span>{similarity}% match</span>
                </button>
              )
            })}
          </div>
          <p className="context-tip">Click a chunk to preview the original PDF page.</p>
        </div>
      )}

      {activeChunk && (
        <Modal onClose={() => setActiveChunk(null)}>
          <div className="modal-header">
            <div>
              <h3>{activeChunk.title}</h3>
              <p>{activeChunk.filename}</p>
            </div>
            <button className="close-btn" onClick={() => {
              if (activeChunk?.objectUrl) URL.revokeObjectURL(activeChunk.objectUrl)
              setActiveChunk(null)
            }}>
              <X size={18} />
            </button>
          </div>
          <iframe src={activeChunk.url} title={activeChunk.title} className="pdf-frame" />
        </Modal>
      )}

      {activeImage && (
        <Modal onClose={() => setActiveImage(null)} contentClassName="image-modal">
          <div className="modal-header">
            <div>
              <h3>{activeImage.title}</h3>
              <p>{activeImage.description}</p>
            </div>
            <button className="close-btn" onClick={() => setActiveImage(null)}>
              <X size={18} />
            </button>
          </div>
          <div className="image-modal-body">
            <img src={activeImage.src} alt={activeImage.title} />
          </div>
        </Modal>
      )}
    </div>
  )
}

export default ResultsDisplay

