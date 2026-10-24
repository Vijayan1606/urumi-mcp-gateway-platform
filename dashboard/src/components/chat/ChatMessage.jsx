import { useState } from "react";
import { Icon } from "../common/Icon";

// Cleanly format inline bold (**text**), italics (*text*), and code (`code`)
function formatInlineText(text) {
  if (!text) return "";

  const parts = [];
  // Match **bold**, *italic*, or `code`
  const regex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const token = match[0];
    if (token.startsWith("**") && token.endsWith("**")) {
      parts.push(
        <strong key={match.index} className="formatted-bold">
          {token.slice(2, -2)}
        </strong>,
      );
    } else if (token.startsWith("*") && token.endsWith("*")) {
      parts.push(
        <span key={match.index} className="formatted-italic">
          {token.slice(1, -1)}
        </span>,
      );
    } else if (token.startsWith("`") && token.endsWith("`")) {
      parts.push(
        <code key={match.index} className="inline-code">
          {token.slice(1, -1)}
        </code>,
      );
    }
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length > 0 ? parts : text;
}

// Render clean lines, bullet lists, and paragraphs with zero raw asterisks
function renderFormattedContent(rawContent) {
  if (!rawContent) return null;

  const lines = String(rawContent).split("\n");

  return (
    <div className="formatted-message-body">
      {lines.map((line, lineIdx) => {
        const trimmed = line.trim();
        if (!trimmed) {
          return <div key={lineIdx} className="line-break-gap" />;
        }

        // Check if line is a bullet item (* or -) and whether it's indented
        const isSubBullet = /^\s{2,}[*-]\s+/.test(line);
        const isBullet = /^[*-]\s+/.test(trimmed) || isSubBullet;

        if (isBullet) {
          // Remove the leading asterisk/dash bullet marker
          const cleanLine = trimmed.replace(/^[*-]\s+/, "");
          return (
            <div
              key={lineIdx}
              className={`formatted-bullet-row ${isSubBullet ? "sub-bullet-row" : ""}`}
            >
              <span className="bullet-symbol" aria-hidden="true">•</span>
              <span className="bullet-content">{formatInlineText(cleanLine)}</span>
            </div>
          );
        }

        // Normal paragraph line
        return (
          <p key={lineIdx} className="formatted-paragraph">
            {formatInlineText(trimmed)}
          </p>
        );
      })}
    </div>
  );
}

// Function to copy pure clean text without raw markdown stars
function getCleanTextForCopy(text) {
  if (!text) return "";
  return String(text)
    .replace(/\*\*(.*?)\*\*/g, "$1") // remove **
    .replace(/\*(.*?)\*/g, "$1")     // remove *
    .replace(/^[*-]\s+/gm, "• ");    // clean bullet
}

export function ChatMessage({ message }) {
  const [copied, setCopied] = useState(false);
  const [showTools, setShowTools] = useState(false);

  const isAssistant = message.role === "assistant";

  const handleCopy = async () => {
    try {
      const cleanText = getCleanTextForCopy(message.content);
      await navigator.clipboard.writeText(cleanText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  const hasToolCalls =
    Array.isArray(message.tool_calls) && message.tool_calls.length > 0;

  return (
    <div
      className={`message-wrapper ${isAssistant ? "assistant-wrap" : "user-wrap"}`}
    >
      <div className="message-avatar-col">
        {isAssistant ? (
          <div className="assistant-avatar message-avatar">
            <span>U</span>
            <span className="avatar-status-pip" />
          </div>
        ) : (
          <div className="avatar message-avatar user-avatar">
            <span>YOU</span>
          </div>
        )}
      </div>

      <div className="message-content-col">
        <div className="message-meta-row">
          <strong className="message-sender-name">
            {isAssistant ? "Urumi AI" : "You"}
          </strong>
          <span className="message-time">
            {message.timestamp || "Just now"}
          </span>
          {isAssistant && hasToolCalls && (
            <button
              type="button"
              className="tool-calls-pill"
              onClick={() => setShowTools(!showTools)}
              title="Click to view MCP tools used"
            >
              <Icon name="tools" size={12} />
              <span>
                {message.tool_calls.length}{" "}
                {message.tool_calls.length === 1 ? "tool used" : "tools used"}
              </span>
              <span className="pill-arrow">{showTools ? "▴" : "▾"}</span>
            </button>
          )}
        </div>

        {/* Collapsible tool calls view */}
        {isAssistant && hasToolCalls && showTools && (
          <div className="tool-calls-details-box">
            <div className="tool-calls-header">
              <Icon name="tools" size={14} />
              <span>Executed Gateway MCP Tools</span>
            </div>
            <ul className="tool-calls-list">
              {message.tool_calls.map((tool, idx) => (
                <li key={idx} className="tool-call-item">
                  <span className="tool-call-name">
                    ⚡ {tool.name || tool.tool || "mcp_tool"}
                  </span>
                  {tool.arguments && (
                    <pre className="tool-call-args">
                      {typeof tool.arguments === "object"
                        ? JSON.stringify(tool.arguments, null, 2)
                        : String(tool.arguments)}
                    </pre>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className={`message-bubble ${message.role}`}>
          <div className="message-text">
            {renderFormattedContent(message.content)}
          </div>
        </div>

        {/* Action bar on hover */}
        <div className="message-actions">
          <button
            type="button"
            className="action-icon-btn"
            onClick={handleCopy}
            title={copied ? "Copied to clipboard!" : "Copy text"}
            aria-label="Copy text"
          >
            {copied ? (
              <span className="copied-tag">✓ Copied</span>
            ) : (
              <span className="copy-label">
                <svg
                  width="13"
                  height="13"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                </svg>
                <span>Copy</span>
              </span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatMessage;
