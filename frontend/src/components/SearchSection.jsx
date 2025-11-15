import { useState } from 'react'
import { Search, Loader2 } from 'lucide-react'
import axios from 'axios'
import './SearchSection.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function SearchSection({ onSearch, isSearching, setIsSearching }) {
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(5)

  const handleSearch = async (e) => {
    e.preventDefault()
    
    if (!query.trim()) {
      return
    }

    setIsSearching(true)
    try {
      const response = await axios.post(
        `${API_URL}/api/search`,
        {
          query: query.trim(),
          top_k: topK,
        },
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      )

      onSearch(response.data)
    } catch (error) {
      console.error('Search error:', error)
      onSearch({
        answer: '',
        sections: [],
        context: [],
        error: error.response?.data?.error || 'Search failed. Please try again.',
      })
    } finally {
      setIsSearching(false)
    }
  }

  return (
    <div className="search-section">
      <div className="section-header">
        <Search size={24} />
        <h2>Search Documents</h2>
      </div>

      <form onSubmit={handleSearch} className="search-form">
        <div className="search-input-group">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your search query..."
            className="search-input"
            disabled={isSearching}
          />
          <button
            type="submit"
            className="search-btn"
            disabled={!query.trim() || isSearching}
          >
            {isSearching ? (
              <Loader2 size={20} className="spinner" />
            ) : (
              <Search size={20} />
            )}
          </button>
        </div>

        <div className="search-options">
          <label>
            Number of results:
            <input
              type="number"
              min="1"
              max="20"
              value={topK}
              onChange={(e) => setTopK(parseInt(e.target.value) || 5)}
              className="top-k-input"
              disabled={isSearching}
            />
          </label>
        </div>
      </form>
    </div>
  )
}

export default SearchSection

