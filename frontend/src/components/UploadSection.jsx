import { useState } from 'react'
import { Upload, FileText, Loader2 } from 'lucide-react'
import axios from 'axios'
import './UploadSection.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function UploadSection({ onUploadSuccess, onUploadError }) {
  const [file, setFile] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile)
    } else {
      onUploadError('Please select a valid PDF file')
    }
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile.type === 'application/pdf') {
        setFile(droppedFile)
      } else {
        onUploadError('Please drop a valid PDF file')
      }
    }
  }

  const handleUpload = async () => {
    if (!file) {
      onUploadError('Please select a file first')
      return
    }

    setIsUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const token = localStorage.getItem('lexivion_token')
      if (!token) {
        onUploadError('Please sign in to upload')
        setIsUploading(false)
        return
      }
      const response = await axios.post(`${API_URL}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`,
        },
        timeout: 300000,
        validateStatus: (status) => status >= 200 && status < 500,
      })

      const data = response.data
      if (response.status === 409 && data.can_replace) {
        const proceed = window.confirm(`This document already exists as "${data.existing_filename}". Replace it?`)
        if (proceed) {
          const repForm = new FormData()
          repForm.append('file', file)
          const repRes = await axios.post(`${API_URL}/api/documents/${data.existing_document_id}/replace`, repForm, {
            headers: {
              'Content-Type': 'multipart/form-data',
              'Authorization': `Bearer ${token}`,
            },
            timeout: 300000,
          })
          const repData = repRes.data
          const msg = repData.message || 'Document replaced successfully'
          onUploadSuccess(`${msg} · chunks: ${repData.chunks_stored}, images: ${repData.images_stored}`)
          setFile(null)
        } else {
          onUploadError('Upload cancelled')
        }
      } else if (response.status >= 200 && response.status < 300) {
        const successMessage = data.message
          ? `${data.message} · chunks: ${data.chunks_stored}, images: ${data.images_stored}`
          : 'File uploaded and processed successfully!'
        onUploadSuccess(successMessage)
        setFile(null)
      } else {
        const errorMessage = data.error || 'Upload failed'
        onUploadError(errorMessage)
      }
      // Reset file input
      const fileInput = document.getElementById('file-input')
      if (fileInput) fileInput.value = ''
    } catch (error) {
      const errorMessage = error.response?.data?.error || error.message || 'Upload failed'
      onUploadError(errorMessage)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="upload-section">
      <div className="section-header">
        <Upload size={24} />
        <h2>Upload PDF Document</h2>
      </div>

      <div
        className={`upload-area ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          id="file-input"
          type="file"
          accept=".pdf"
          onChange={handleFileSelect}
          className="file-input"
          disabled={isUploading}
        />
        
        {!file ? (
          <div className="upload-placeholder">
            <FileText size={48} />
            <p>Drag and drop a PDF file here, or click to browse</p>
            <span className="upload-hint">Only PDF files are supported</span>
          </div>
        ) : (
          <div className="file-selected">
            <FileText size={32} />
            <div className="file-info">
              <p className="file-name">{file.name}</p>
              <p className="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
          </div>
        )}
      </div>

      <button
        className="upload-btn"
        onClick={handleUpload}
        disabled={!file || isUploading}
      >
        {isUploading ? (
          <>
            <Loader2 size={20} className="spinner" />
            Processing PDF...
          </>
        ) : (
          <>
            <Upload size={20} />
            Upload & Process
          </>
        )}
      </button>
    </div>
  )
}

export default UploadSection

