import { FC } from 'react'
import styles from './LoadingIndicator.module.css'

interface LoadingIndicatorProps {
  progress?: number
  message?: string
}

const LoadingIndicator: FC<LoadingIndicatorProps> = ({
  progress = 0,
  message = 'Extracting text from PDF...'
}) => {
  const normalizedProgress = Math.min(Math.max(progress, 0), 100)
  const hasProgress = normalizedProgress > 0

  return (
    <div className={styles.container} role="status" aria-live="polite" aria-label="Loading">
      {/* Animated spinner */}
      <div className={styles.spinnerContainer}>
        <svg
          className={styles.spinner}
          width="64"
          height="64"
          viewBox="0 0 50 50"
        >
          <circle
            className={styles.spinnerTrack}
            cx="25"
            cy="25"
            r="20"
            fill="none"
            strokeWidth="4"
          />
          <circle
            className={styles.spinnerPath}
            cx="25"
            cy="25"
            r="20"
            fill="none"
            strokeWidth="4"
            strokeDasharray={hasProgress ? `${normalizedProgress * 1.256} 125.6` : undefined}
          />
        </svg>
      </div>

      {/* Loading message */}
      <div className={styles.content}>
        <p className={styles.message}>{message}</p>

        {/* Progress percentage */}
        {hasProgress && (
          <div className={styles.progressInfo}>
            <span className={styles.percentage}>{Math.round(normalizedProgress)}%</span>
            <div className={styles.progressBar}>
              <div
                className={styles.progressFill}
                style={{ width: `${normalizedProgress}%` }}
                role="progressbar"
                aria-valuenow={normalizedProgress}
                aria-valuemin={0}
                aria-valuemax={100}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default LoadingIndicator
