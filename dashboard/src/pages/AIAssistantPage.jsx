import { PageHeading } from "../components/common/PageHeading";
import { ChatWindow } from "../components/chat/ChatWindow";

export function AIAssistantPage({
  messages,
  setMessages,
  onSendMessage,
  isLoading,
  apiKey,
}) {
  return (
    <div className="page-view animate-fade-in chat-page-view">
      <PageHeading
        eyebrow="AI PLAYGROUND"
        title="Urumi Assistant"
        subtitle="Conversational interface powered by Gemini AI and connected MCP upstream tools."
      />

      <ChatWindow
        messages={messages}
        setMessages={setMessages}
        onSendMessage={onSendMessage}
        isLoading={isLoading}
        apiKey={apiKey}
      />
    </div>
  );
}

export default AIAssistantPage;
