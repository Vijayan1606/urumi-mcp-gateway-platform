export function LoadingSpinner({ size = 18, color = "currentColor", className = "" }) {
  return (
    <svg
      className={`loading-spinner ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}

export function TypingIndicator({ label = "Urumi AI is thinking..." }) {
  return (
    <div className="typing-indicator-wrapper" aria-live="polite">
      <div className="typing-dots">
        <span className="dot dot-1" />
        <span className="dot dot-2" />
        <span className="dot dot-3" />
      </div>
      {label && <span className="typing-label">{label}</span>}
    </div>
  );
}

export default LoadingSpinner;
