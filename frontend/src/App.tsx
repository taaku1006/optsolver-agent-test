import './App.css'
import { useState } from 'react'
import DragDropZone from './components/DragDropZone'
import LoadingIndicator from './components/LoadingIndicator'
import ErrorDisplay from './components/ErrorDisplay'
import type { ErrorType } from './components/ErrorDisplay'

function App() {
  const [showLoading, setShowLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [showError, setShowError] = useState(false)
  const [errorType, setErrorType] = useState<ErrorType>('CORRUPTED_PDF')

  const handleFileSelect = (_file: File) => {
    // Simulate PDF extraction process for verification
    setShowLoading(true)
    setProgress(0)
    setShowError(false)

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

  const handleShowError = (type: ErrorType) => {
    setShowLoading(false)
    setShowError(true)
    setErrorType(type)
  }

  const handleRetry = () => {
    setShowError(false)
  }

  const getErrorMessage = () => {
    switch (errorType) {
      case 'CORRUPTED_PDF':
        return 'The PDF file appears to be damaged and cannot be read.'
      case 'PASSWORD_PROTECTED':
        return 'This PDF file is password protected and cannot be processed.'
      case 'EXTRACTION_FAILED':
        return 'Failed to extract text from the PDF. The file may contain only scanned images.'
      case 'INVALID_TYPE':
        return 'Only PDF files are supported. Please upload a valid PDF file.'
      case 'FILE_TOO_LARGE':
        return 'The file exceeds the maximum allowed size of 50MB.'
      case 'NETWORK_ERROR':
        return 'Unable to connect to the server. Please check your internet connection.'
      default:
        return 'An unexpected error occurred while processing the file.'
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>OptSolver - PDF Upload & Analysis</h1>
        <p>Upload research papers for automated analysis</p>
      </header>
      <main className="app-main">
        {/* Error test buttons */}
        <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap', justifyContent: 'center' }}>
          <button onClick={() => handleShowError('CORRUPTED_PDF')}>Test Corrupted PDF</button>
          <button onClick={() => handleShowError('PASSWORD_PROTECTED')}>Test Password Protected</button>
          <button onClick={() => handleShowError('EXTRACTION_FAILED')}>Test Extraction Failed</button>
          <button onClick={() => handleShowError('INVALID_TYPE')}>Test Invalid Type</button>
          <button onClick={() => handleShowError('FILE_TOO_LARGE')}>Test File Too Large</button>
          <button onClick={() => handleShowError('NETWORK_ERROR')}>Test Network Error</button>
        </div>

        {showError ? (
          <ErrorDisplay
            error={getErrorMessage()}
            errorType={errorType}
            onRetry={handleRetry}
            showRetry={true}
            showDismiss={false}
          />
        ) : showLoading ? (
          <LoadingIndicator progress={progress} />
        ) : (
          <DragDropZone onFileSelect={handleFileSelect} />
        )}
      </main>
    </div>
  )
}

export default App
