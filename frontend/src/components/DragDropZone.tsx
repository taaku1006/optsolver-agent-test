import { useState, useRef, DragEvent, ChangeEvent, FC } from 'react'
import styles from './DragDropZone.module.css'
import { validateFile } from '../utils/fileValidation'
import type { FileValidationError } from '../types/upload'

interface DragDropZoneProps {
  onFileSelect: (file: File) => void
  accept?: string
  disabled?: boolean
  maxSizeInMB?: number
  onValidationError?: (error: FileValidationError) => void
}

const DragDropZone: FC<DragDropZoneProps> = ({
  onFileSelect,
  accept = '.pdf',
  disabled = false,
  maxSizeInMB = 50,
  onValidationError
}) => {
  const [isDragging, setIsDragging] = useState(false)
  const [validationError, setValidationError] = useState<FileValidationError | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    if (!disabled) {
      setIsDragging(true)
    }
  }

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()

    // Only set dragging to false if we're leaving the drop zone itself
    // not just moving between child elements
    const rect = e.currentTarget.getBoundingClientRect()
    const x = e.clientX
    const y = e.clientY

    if (x <= rect.left || x >= rect.right || y <= rect.top || y >= rect.bottom) {
      setIsDragging(false)
    }
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleFileValidation = (file: File) => {
    // Clear any previous errors
    setValidationError(null)

    // Validate the file
    const validationResult = validateFile(file, { maxSizeInMB })

    if (!validationResult.isValid && validationResult.error) {
      setValidationError(validationResult.error)
      if (onValidationError) {
        onValidationError(validationResult.error)
      }
      return
    }

    // File is valid, pass it to parent
    onFileSelect(file)
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    if (disabled) return

    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      handleFileValidation(files[0])
    }
  }

  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileValidation(files[0])
    }
    // Reset input value so same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleClick = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click()
    }
  }

  return (
    <div
      className={`${styles.dropzone} ${isDragging ? styles.dragging : ''} ${disabled ? styles.disabled : ''}`}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={handleClick}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label="Upload PDF file"
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
          e.preventDefault()
          handleClick()
        }
      }}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        onChange={handleFileInputChange}
        className={styles.fileInput}
        disabled={disabled}
        aria-hidden="true"
      />

      <div className={styles.content}>
        <svg
          className={styles.icon}
          width="64"
          height="64"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>

        <div className={styles.text}>
          <p className={styles.primary}>
            {isDragging ? 'Drop PDF file here' : 'Drag & drop PDF file here'}
          </p>
          <p className={styles.secondary}>
            or click to browse
          </p>
          <p className={styles.hint}>
            Maximum file size: {maxSizeInMB}MB
          </p>
        </div>

        {validationError && (
          <div className={styles.error} role="alert" aria-live="polite">
            <svg
              className={styles.errorIcon}
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span className={styles.errorMessage}>{validationError.message}</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default DragDropZone
