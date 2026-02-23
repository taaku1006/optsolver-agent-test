import './App.css'
import { useState } from 'react'
import DragDropZone from './components/DragDropZone'
import LoadingIndicator from './components/LoadingIndicator'

function App() {
  const [showLoading, setShowLoading] = useState(false)
  const [progress, setProgress] = useState(0)

  const handleFileSelect = (_file: File) => {
    // Simulate PDF extraction process for verification
    setShowLoading(true)
    setProgress(0)

    // Simulate progress updates
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval)
          setTimeout(() => {
            setShowLoading(false)
            setProgress(0)
          }, 500)
          return 100
        }
        return prev + 10
      })
    }, 300)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>OptSolver - PDF Upload & Analysis</h1>
        <p>Upload research papers for automated analysis</p>
      </header>
      <main className="app-main">
        {showLoading ? (
          <LoadingIndicator progress={progress} />
        ) : (
          <DragDropZone onFileSelect={handleFileSelect} />
        )}
      </main>
    </div>
  )
}

export default App
