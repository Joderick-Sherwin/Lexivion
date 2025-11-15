import { useState } from 'react'
import { FileText, CheckCircle2, AlertCircle, X, Sparkles, Compass, ImageIcon } from 'lucide-react'
import './App.css'
import UploadSection from './components/UploadSection'
import SearchSection from './components/SearchSection'
import ResultsDisplay from './components/ResultsDisplay'
import AuthSection from './components/AuthSection'

const InsightCard = ({ label, value, sublabel, icon }) => (
  <div className="insight-card">
    <div className="insight-icon">{icon}</div>
    <div>
      <p>{label}</p>
      <h4>{value}</h4>
      <span>{sublabel}</span>
    </div>
  </div>
)

function App() {
  const [uploadStatus, setUploadStatus] = useState(null)
  const [searchResult, setSearchResult] = useState(null)
  const [isSearching, setIsSearching] = useState(false)
  const [auth, setAuth] = useState(null)

  const totalChunks = searchResult?.context?.length ?? 0
  const sectionsCount = searchResult?.sections?.length ?? 0
  const totalImages = searchResult?.sections?.reduce(
    (sum, section) => sum + (section.images?.length || 0),
    0
  ) ?? 0
  const uniqueDocuments = searchResult
    ? new Set(
        searchResult.context
          ?.map((ctx) => ctx.document?.id)
          .filter((id) => Boolean(id))
      ).size
    : 0

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <FileText size={32} />
            <h1>Lexivion</h1>
          </div>
          <p className="subtitle">Advanced Document Search with AI</p>
          {auth && (
            <div className="user-actions">
              <div className="user-chip">
                <span>{auth.email}</span>
              </div>
              <button
                className="signout-btn"
                onClick={() => {
                  localStorage.removeItem('lexivion_token')
                  localStorage.removeItem('lexivion_user_email')
                  setAuth(null)
                  setSearchResult(null)
                  setUploadStatus(null)
                }}
              >
                Sign Out
              </button>
            </div>
          )}
        </div>
      </header>

      <main className="app-main">
        <div className="container">
          {!auth ? (
            <div className="auth-page">
              <AuthSection onAuthChange={(info) => setAuth(info)} />
            </div>
          ) : (
            <div className="workspace-grid">
              <UploadSection 
                onUploadSuccess={(message) => {
                  setUploadStatus({ type: 'success', message })
                  setSearchResult(null)
                }}
                onUploadError={(error) => {
                  setUploadStatus({ type: 'error', message: error })
                }}
              />

              <div className="right-panel">
                {uploadStatus && (
                  <div className={`status-banner ${uploadStatus.type}`}>
                    {uploadStatus.type === 'success' ? (
                      <CheckCircle2 size={20} />
                    ) : (
                      <AlertCircle size={20} />
                    )}
                    <span>{uploadStatus.message}</span>
                    <button 
                      className="close-btn"
                      onClick={() => setUploadStatus(null)}
                    >
                      <X size={16} />
                    </button>
                  </div>
                )}

                <SearchSection
                  onSearch={(results) => {
                    setSearchResult(results)
                    setUploadStatus(null)
                  }}
                  isSearching={isSearching}
                  setIsSearching={setIsSearching}
                />
              </div>
            </div>
          )}

          {searchResult && (
            <>
              <div className="insight-grid">
                <InsightCard
                  label="Matched Chunks"
                  value={totalChunks}
                  sublabel="Context segments powering Gemini"
                  icon={<Sparkles size={20} />}
                />
                <InsightCard
                  label="Sections Synthesized"
                  value={sectionsCount}
                  sublabel="Structured response groups"
                  icon={<Compass size={20} />}
                />
                <InsightCard
                  label="Documents Linked"
                  value={uniqueDocuments}
                  sublabel="Source PDFs in this answer"
                  icon={<FileText size={20} />}
                />
                <InsightCard
                  label="Images Surfaced"
                  value={totalImages}
                  sublabel="Visual context pulled alongside text"
                  icon={<ImageIcon size={20} />}
                />
              </div>
              <ResultsDisplay result={searchResult} />
            </>
          )}
        </div>
      </main>

      <footer className="app-footer">
        <p>Lexivion - Advanced AI-Powered Document Intelligence</p>
      </footer>
    </div>
  )
}

export default App

