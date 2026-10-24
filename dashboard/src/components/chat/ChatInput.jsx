import { useRef, useEffect } from "react";
import { LoadingSpinner } from "../common/LoadingSpinner";

export function ChatInput({
  input,
  setInput,
  onSubmit,
  isLoading,
  suggestions = [],
  onSelectSuggestion,
  disabled = false,
}) {
  const inputRef = useRef(null);

  useEffect(() => {
    if (!isLoading && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isLoading]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit(e);
    }
  };

  return (
    <div className="chat-input-container">
      {suggestions.length > 0 && (
        <div className="suggestion-row">
          <span className="suggestion-label">Suggested:</span>
          {suggestions.map((prompt, index) => (
            <button
              type="button"
              key={index}
              className="suggestion-chip"
              onClick={() => onSelectSuggestion(prompt)}
              disabled={isLoading || disabled}
            >
              <span className="chip-sparkle">✦</span>
              <span>{prompt}</span>
            </button>
          ))}
        </div>
      )}

      <form className="chat-form" onSubmit={onSubmit}>
        <div className="chat-input-wrapper">
          <input
            ref={inputRef}
            type="text"
            className="chat-text-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              disabled
                ? "Connect your gateway API key to chat with Urumi AI..."
                : "Ask about products, orders, inventory stock, or customer support..."
            }
            disabled={isLoading || disabled}
            aria-label="Ask Urumi AI"
          />

          {input.length > 0 && !isLoading && (
            <button
              type="button"
              className="clear-input-btn"
              onClick={() => setInput("")}
              title="Clear query"
              aria-label="Clear input"
            >
              ✕
            </button>
          )}
        </div>

        <button
          type="submit"
          className="chat-send-btn primary-button"
          disabled={!input.trim() || isLoading || disabled}
          aria-label="Send message"
        >
          {isLoading ? (
            <LoadingSpinner size={16} />
          ) : (
            <>
              <span>Send</span>
              <span className="send-arrow" aria-hidden="true">
                ↑
              </span>
            </>
          )}
        </button>
      </form>

      <div className="chat-input-footer">
        <span>Press <kbd>Enter ↵</kbd> to send</span>
        <span>Powered by Gemini AI · Urumi MCP Gateway</span>
      </div>
    </div>
  );
}

export default ChatInput;
