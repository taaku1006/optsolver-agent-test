import { FC } from 'react'
import styles from './TextPreview.module.css'
import type { PDFExtractionResult } from '../types/pdf'

interface TextPreviewProps {
  result: PDFExtractionResult
  maxHeight?: string
}

const TextPreview: FC<TextPreviewProps> = ({ result, maxHeight = '600px' }) => {
  const { text, pageCount, metadata } = result

  return (
    <div className={styles.container}>
      {/* Metadata section */}
      {metadata && (
        <div className={styles.metadata}>
          <h3 className={styles.metadataTitle}>Document Information</h3>
          <div className={styles.metadataGrid}>
            {metadata.title && (
              <div className={styles.metadataItem}>
                <span className={styles.metadataLabel}>Title:</span>
                <span className={styles.metadataValue}>{metadata.title}</span>
              </div>
            )}
            {metadata.author && (
              <div className={styles.metadataItem}>
                <span className={styles.metadataLabel}>Author:</span>
                <span className={styles.metadataValue}>{metadata.author}</span>
              </div>
            )}
            <div className={styles.metadataItem}>
              <span className={styles.metadataLabel}>Pages:</span>
              <span className={styles.metadataValue}>{pageCount}</span>
            </div>
            {metadata.creationDate && (
              <div className={styles.metadataItem}>
                <span className={styles.metadataLabel}>Created:</span>
                <span className={styles.metadataValue}>
                  {new Date(metadata.creationDate).toLocaleDateString()}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Text preview section */}
      <div className={styles.textSection}>
        <div className={styles.textHeader}>
          <h3 className={styles.textTitle}>Extracted Text</h3>
          <span className={styles.textCount}>
            {text.length.toLocaleString()} characters
          </span>
        </div>
        <div
          className={styles.textContent}
          style={{ maxHeight }}
          role="region"
          aria-label="Extracted PDF text"
          tabIndex={0}
        >
          <pre className={styles.textPre}>{text}</pre>
        </div>
      </div>
    </div>
  )
}

export default TextPreview
