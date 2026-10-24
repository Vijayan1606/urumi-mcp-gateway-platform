import { useState, useEffect, useRef } from "react";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";

const SUGGESTIONS = [
  "List my store products",
  "Check inventory stock",
  "Show today's orders",
  "What MCP tools are available?",
];

export function ChatWindow({
  messages = [],
  setMessages,
  onSendMessage,
  isLoading = false,
  apiKey = "",
}) {
  const [chatInput, setChatInput] = useState("");
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of chat whenever messages change or loading state changes
  const scrollToBottom = (behavior = "smooth") => {
    messagesEndRef.current?.scrollIntoView({ behavior, block: "end" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleFormSubmit = (e) => {
    e?.preventDefault?.();
    const query = chatInput.trim();
    if (!query || isLoading) return;

    onSendMessage(query);
    setChatInput("");
  };

  const handleClearHistory = () => {
    setMessages([
      {
        role: "assistant",
        content:
          "Chat history cleared. How can I help with your products, store orders, or inventory?",
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      },
    ]);
  };

  return (
    <section className="chat-panel">
      {/* Top chat banner */}
      <div className="chat-top">
        <div className="chat-top-left">
          <div className="assistant-avatar">
            <span>U</span>
            <span className="avatar-pulse-ring" />
          </div>
          <div className="chat-assistant-meta">
            <div className="assistant-title-row">
              <strong>Urumi AI Assistant</strong>
              <span className="badge-model">Gemini 2.5 Flash</span>
            </div>
            {/* WhatsApp-style typing status in the header */}
            <span className="chat-sub-status">
              {isLoading ? (
                <span className="whatsapp-typing-text">
                  typing<span className="dot-anim-1">.</span><span className="dot-anim-2">.</span><span className="dot-anim-3">.</span>
                </span>
              ) : apiKey ? (
                "Live Gateway Active · MCP Integrated"
              ) : (
                "Demo Mode · Connect Gateway API Key"
              )}
            </span>
          </div>
        </div>

        <div className="chat-top-actions">
          <button
            type="button"
            className="secondary-button btn-sm clear-chat-btn"
            onClick={handleClearHistory}
            title="Clear current chat messages"
          >
            Clear chat
          </button>
          <span
            className={`status-dot ${apiKey ? "dot-connected" : "dot-disconnected"}`}
            title={apiKey ? "Gateway connected" : "Gateway disconnected"}
          />
        </div>
      </div>

      {/* Messages viewport */}
      <div className="chat-messages" role="log" aria-live="polite">
        {messages.map((message, index) => (
          <ChatMessage
            key={`${message.role}-${index}-${message.timestamp || index}`}
            message={message}
          />
        ))}

        {/* WhatsApp-style typing bubble while awaiting agent response */}
        {isLoading && (
          <div className="message-wrapper assistant-wrap whatsapp-typing-wrap animate-fade-in">
            <div className="message-avatar-col">
              <div className="assistant-avatar message-avatar">
                <span>U</span>
              </div>
            </div>
            <div className="message-content-col">
              <div className="message-meta-row">
                <strong className="message-sender-name">Urumi AI</strong>
                <span className="whatsapp-typing-badge">typing...</span>
              </div>
              <div className="message-bubble assistant whatsapp-typing-bubble">
                <div className="whatsapp-dots">
                  <span className="w-dot w-dot-1" />
                  <span className="w-dot w-dot-2" />
                  <span className="w-dot w-dot-3" />
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Chat input form */}
      <ChatInput
        input={chatInput}
        setInput={setChatInput}
        onSubmit={handleFormSubmit}
        isLoading={isLoading}
        suggestions={SUGGESTIONS}
        onSelectSuggestion={(suggestion) => setChatInput(suggestion)}
        disabled={false}
      />
    </section>
  );
}

export default ChatWindow;
