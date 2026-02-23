import './App.css'
import PDFUploader from './components/PDFUploader'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>OptSolver - PDF Upload & Analysis</h1>
        <p>Upload research papers for automated analysis</p>
      </header>
      <main className="app-main">
        <PDFUploader />
      </main>
    </div>
  )
}

export default App
