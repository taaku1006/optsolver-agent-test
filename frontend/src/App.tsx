import './App.css'
import DragDropZone from './components/DragDropZone'

function App() {
  const handleFileSelect = (_file: File) => {
    // File selection handling will be implemented in later phases
    // For now, this demonstrates the component integration
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>OptSolver - PDF Upload & Analysis</h1>
        <p>Upload research papers for automated analysis</p>
      </header>
      <main className="app-main">
        <DragDropZone onFileSelect={handleFileSelect} />
      </main>
    </div>
  )
}

export default App
