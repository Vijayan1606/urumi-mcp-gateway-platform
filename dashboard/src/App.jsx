import { useEffect, useState } from "react";
import AppLayout from "./components/layouts/AppLayout";
import OverviewPage from "./pages/OverviewPage";
import MCPServersPage from "./pages/MCPServersPage";
import ToolsPage from "./pages/ToolsPage";
import TeamMembersPage from "./pages/TeamMembersPage";
import APIKeysPage from "./pages/APIKeysPage";
import AuditLogsPage from "./pages/AuditLogsPage";
import AIAssistantPage from "./pages/AIAssistantPage";
import {
  getServers,
  getUpstreamHealth,
  getTools,
  getAuditLogs,
  updateServerStatus,
  getUsers,
  createUser,
  getApiKeys,
  createApiKey,
  revokeApiKey,
  sendChatMessage,
} from "./services/api";
import "./App.css";

const initialServers = [
  {
    name: "WooCommerce",
    description: "Product and order management",
    status: "Healthy",
    enabled: true,
    tools: 5,
  },
  {
    name: "Inventory",
    description: "Inventory and stock management",
    status: "Healthy",
    enabled: true,
    tools: 3,
  },
  {
    name: "Customer Support",
    description: "FAQs and support tickets",
    status: "Disabled",
    enabled: false,
    tools: 3,
  },
];

const initialTools = [
  {
    name: "wc_list_products",
    server: "woocommerce",
    description: "Fetch paginated product catalog with pricing and stock levels",
  },
  {
    name: "wc_get_orders",
    server: "woocommerce",
    description: "Retrieve recent customer orders, fulfillment status, and totals",
  },
  {
    name: "wc_update_order_status",
    server: "woocommerce",
    description: "Transition order state to processing, completed, or refunded",
  },
  {
    name: "inv_check_stock",
    server: "inventory",
    description: "Check real-time warehouse inventory for a specific SKU",
  },
  {
    name: "inv_reserve_item",
    server: "inventory",
    description: "Hold warehouse units pending order confirmation",
  },
  {
    name: "support_search_kb",
    server: "customer_support",
    description: "Query company knowledge base for policy and shipping answers",
  },
];

const initialAuditLogs = [
  {
    id: 1,
    user: "admin@urumi.internal",
    server: "WooCommerce",
    tool: "wc_list_products",
    outcome: "Success",
    duration: "142ms",
  },
  {
    id: 2,
    user: "api_key#cursor",
    server: "Inventory",
    tool: "inv_check_stock",
    outcome: "Success",
    duration: "89ms",
  },
  {
    id: 3,
    user: "agent@support",
    server: "Customer Support",
    tool: "support_search_kb",
    outcome: "Failure",
    duration: "520ms",
  },
];

function App() {
  const [apiKey, setApiKey] = useState("");
  const [keyInput, setKeyInput] = useState("");
  const [connectionStatus, setConnectionStatus] = useState("Disconnected");
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState("");
  const [auditLogs, setAuditLogs] = useState(initialAuditLogs);
  const [tools, setTools] = useState(initialTools);
  const [teamMembers, setTeamMembers] = useState([]);
  const [managedKeys, setManagedKeys] = useState([]);
  const [teamEmail, setTeamEmail] = useState("");
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyUserId, setNewKeyUserId] = useState("");
  const [newlyCreatedKey, setNewlyCreatedKey] = useState("");
  const [managementLoading, setManagementLoading] = useState(false);
  const [managementError, setManagementError] = useState("");
  const [managementMessage, setManagementMessage] = useState("");
  const [activePage, setActivePage] = useState("Overview");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [servers, setServers] = useState(initialServers);
  const [upstreamHealth, setUpstreamHealth] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Welcome to Urumi MCP Playground! I can execute tools against your connected upstream servers. Ask me to list products, check stock, or review recent orders.",
      timestamp: "10:00 AM",
      skipAnimation: true,
    },
  ]);

  // Clear one-time secrets when navigating away from API Keys
  useEffect(() => {
    if (activePage !== "API Keys") {
      setNewlyCreatedKey("");
    }
  }, [activePage]);

  // Periodic upstream health polling when authenticated
  useEffect(() => {
    if (!apiKey) {
      setUpstreamHealth([]);
      return;
    }

    let cancelled = false;

    async function refreshUpstreamHealth() {
      try {
        const data = await getUpstreamHealth(apiKey);
        const healthList = Array.isArray(data) ? data : (data?.servers ?? []);

        if (cancelled) return;

        setUpstreamHealth(healthList);

        setServers((currentServers) =>
          currentServers.map((server) => {
            const health = healthList.find(
              (item) => item.name === (server.serverKey || server.name),
            );

            let status = "Unknown";
            if (!server.enabled) {
              status = "Disabled";
            } else if (health?.status === "healthy") {
              status = "Healthy";
            } else if (health?.status === "unreachable") {
              status = "Unreachable";
            } else if (health?.status === "disabled") {
              status = "Disabled";
            }

            return { ...server, status };
          }),
        );
      } catch {
        // Keep last known status
      }
    }

    refreshUpstreamHealth();
    const intervalId = window.setInterval(refreshUpstreamHealth, 15000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [apiKey]);

  async function loadTeamMembers(key = apiKey) {
    if (!key) return;
    try {
      const data = await getUsers(key);
      setTeamMembers(Array.isArray(data) ? data : (data.users ?? []));
    } catch (error) {
      setManagementError(error.message || "Could not load team members.");
    }
  }

  async function loadManagedKeys(key = apiKey) {
    if (!key) return;
    try {
      const data = await getApiKeys(key);
      setManagedKeys(Array.isArray(data) ? data : (data.keys ?? []));
    } catch (error) {
      setManagementError(error.message || "Could not load API keys.");
    }
  }

  async function handleCreateApiKey(event) {
    event.preventDefault();
    setManagementError("");
    setManagementMessage("");
    setNewlyCreatedKey("");

    if (!newKeyName.trim()) {
      setManagementError("Enter a name for the API key.");
      return;
    }

    setManagementLoading(true);

    try {
      const result = await createApiKey(
        apiKey,
        newKeyName.trim(),
        newKeyUserId === "" ? undefined : Number(newKeyUserId),
      );

      const candidates = [
        result?.key,
        result?.api_key,
        result?.raw_key,
        result?.secret,
      ];
      const rawKey = candidates.find((value) => typeof value === "string");
      if (rawKey) {
        setNewlyCreatedKey(rawKey);
      }

      setNewKeyName("");
      setNewKeyUserId("");
      setManagementMessage(
        rawKey
          ? "API key created. Copy it now; it will not be shown again."
          : "API key created successfully.",
      );
      await loadManagedKeys(apiKey);
    } catch (error) {
      setManagementError(error.message || "Could not create API key.");
    } finally {
      setManagementLoading(false);
    }
  }

  async function handleRevokeApiKey(keyId) {
    const confirmed = window.confirm(
      `Revoke API key #${keyId}? Any client using it will lose access immediately.`,
    );

    if (!confirmed) return;

    setManagementError("");
    setManagementMessage("");
    setNewlyCreatedKey("");
    setManagementLoading(true);

    try {
      await revokeApiKey(apiKey, keyId);
      setManagementMessage(`API key #${keyId} successfully revoked.`);
      await loadManagedKeys(apiKey);
    } catch (error) {
      setManagementError(error.message || "Could not revoke API key.");
    } finally {
      setManagementLoading(false);
    }
  }

  async function handleCreateMember(event) {
    event.preventDefault();
    setManagementError("");
    setManagementMessage("");

    if (!teamEmail.trim()) {
      setManagementError("Enter the member's email address.");
      return;
    }

    setManagementLoading(true);

    try {
      await createUser(apiKey, teamEmail.trim());
      setTeamEmail("");
      setManagementMessage("Team member account created successfully.");
      await loadTeamMembers(apiKey);
    } catch (error) {
      setManagementError(error.message || "Could not create team member.");
    } finally {
      setManagementLoading(false);
    }
  }

  async function connectGateway(event) {
    event.preventDefault();
    const enteredKey = keyInput.trim();

    if (!enteredKey) {
      setApiError("Please enter your gateway API key.");
      return;
    }

    setLoading(true);
    setApiError("");

    try {
      const [serverData, toolData, auditData, healthData] = await Promise.all([
        getServers(enteredKey),
        getTools(enteredKey),
        getAuditLogs(enteredKey).catch(() => []),
        getUpstreamHealth(enteredKey).catch(() => null),
      ]);

      const healthList = Array.isArray(healthData)
        ? healthData
        : (healthData?.servers ?? []);
      setUpstreamHealth(healthList);

      const [userData, keyData] = await Promise.all([
        getUsers(enteredKey).catch(() => []),
        getApiKeys(enteredKey).catch(() => []),
      ]);

      setTeamMembers(Array.isArray(userData) ? userData : (userData?.users ?? []));
      setManagedKeys(Array.isArray(keyData) ? keyData : (keyData?.keys ?? []));

      const serverList = Array.isArray(serverData)
        ? serverData
        : (serverData.servers ?? []);
      const toolList = Array.isArray(toolData)
        ? toolData
        : (toolData.tools ?? []);

      setServers(serverList.length ? serverList : initialServers);
      setTools(toolList.length ? toolList : initialTools);
      setAuditLogs(Array.isArray(auditData) ? auditData : initialAuditLogs);

      setApiKey(enteredKey);
      setConnectionStatus("Connected");
      setApiError("");
    } catch (error) {
      setApiError(error.message || "Failed to authenticate with gateway.");
      setConnectionStatus("Disconnected");
    } finally {
      setLoading(false);
    }
  }

  function handleDisconnect() {
    setApiKey("");
    setKeyInput("");
    setConnectionStatus("Disconnected");
    setApiError("");
    setManagementError("");
    setManagementMessage("");
    setNewlyCreatedKey("");
    setTeamMembers([]);
    setManagedKeys([]);
    setServers(initialServers);
    setTools(initialTools);
    setAuditLogs(initialAuditLogs);
  }

  async function toggleServer(serverName) {
    const target = servers.find((s) => s.name === serverName);
    const newEnabled = !target?.enabled;

    setServers((currentServers) =>
      currentServers.map((server) => {
        if (server.name === serverName) {
          return {
            ...server,
            enabled: newEnabled,
            status: newEnabled ? "Healthy" : "Disabled",
          };
        }
        return server;
      }),
    );

    if (apiKey) {
      try {
        await updateServerStatus(apiKey, serverName, newEnabled);
        const toolsData = await getTools(apiKey).catch(() => null);
        if (toolsData) {
          const list = Array.isArray(toolsData) ? toolsData : (toolsData.tools ?? []);
          setTools(list);
        }
      } catch (err) {
        console.error("Failed to toggle server on gateway:", err);
      }
    }
  }

  async function handleSendMessage(question) {
    if (!question || isLoading) return;

    const timeStr = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    // Display the user's query immediately
    setMessages((current) => [
      ...current,
      { role: "user", content: question, timestamp: timeStr },
    ]);

    setIsLoading(true);

    try {
      if (!apiKey) {
        // Engaging simulator if disconnected so the user can see typing animations instantly!
        await new Promise((resolve) => setTimeout(resolve, 950));

        let mockReply = "";
        let mockTools = [];

        const lowerQ = question.toLowerCase();
        if (lowerQ.includes("product") || lowerQ.includes("store")) {
          mockTools = [{ name: "wc_list_products", arguments: { limit: 5 } }];
          mockReply = `I queried WooCommerce using **wc_list_products**:\n\n1. **Urumi Organic Silk Scarf** — $48.00 (In Stock: 14)\n2. **Handcrafted Copper Flask** — $65.00 (In Stock: 8)\n3. **Ceramic Pour-Over Mug** — $24.00 (In Stock: 32)\n\nAll 3 items are active and ready for shipping. Would you like me to inspect fulfillment or stock alerts?`;
        } else if (lowerQ.includes("stock") || lowerQ.includes("inventory")) {
          mockTools = [{ name: "inv_check_stock", arguments: { sku: "ALL_ACTIVE" } }];
          mockReply = `Checked warehouse inventory via **inv_check_stock**:\n\n• **Total SKUs tracked**: 428 items\n• **Low stock alerts**: 2 items below safety threshold\n• **Pending warehouse inbound**: 50 units arriving tomorrow.\n\nEverything else is well within safe operational buffers.`;
        } else if (lowerQ.includes("order")) {
          mockTools = [{ name: "wc_get_orders", arguments: { period: "today" } }];
          mockReply = `Retrieved today's order metrics via **wc_get_orders**:\n\n• **18 new orders** placed today ($1,420.50 gross)\n• **14 orders** fulfilled & tracking dispatched\n• **4 orders** currently in processing queue.\n\nNo escalated fulfillment delays recorded.`;
        } else {
          mockReply = `I received your request: "${question}". I am connected to the WooCommerce, Inventory, and Support MCP servers. To stream live production data, paste your Gateway API key in the connection bar above!`;
        }

        setMessages((current) => [
          ...current,
          {
            role: "assistant",
            content: mockReply,
            tool_calls: mockTools,
            timestamp: new Date().toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            }),
          },
        ]);
        return;
      }

      // Live backend call with API key
      const result = await sendChatMessage(apiKey, question);

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: result.answer || "Query processed with no message content.",
          tool_calls: result.tool_calls || [],
          timestamp: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: `Sorry, I couldn't complete your request: ${error.message || "Failed to reach gateway."}`,
          timestamp: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  function renderCurrentPage() {
    switch (activePage) {
      case "Overview":
        return (
          <OverviewPage
            servers={servers}
            tools={tools}
            auditLogs={auditLogs}
            upstreamHealth={upstreamHealth}
            apiKey={apiKey}
            setActivePage={setActivePage}
          />
        );
      case "MCP Servers":
        return (
          <MCPServersPage
            servers={servers}
            onToggleServer={toggleServer}
            apiKey={apiKey}
          />
        );
      case "Tools":
        return <ToolsPage tools={tools} apiKey={apiKey} />;
      case "Team Members":
        return (
          <TeamMembersPage
            teamMembers={teamMembers}
            teamEmail={teamEmail}
            setTeamEmail={setTeamEmail}
            onCreateMember={handleCreateMember}
            onRefreshMembers={() => loadTeamMembers()}
            managementLoading={managementLoading}
            managementError={managementError}
            managementMessage={managementMessage}
            apiKey={apiKey}
          />
        );
      case "API Keys":
        return (
          <APIKeysPage
            managedKeys={managedKeys}
            teamMembers={teamMembers}
            newKeyName={newKeyName}
            setNewKeyName={setNewKeyName}
            newKeyUserId={newKeyUserId}
            setNewKeyUserId={setNewKeyUserId}
            newlyCreatedKey={newlyCreatedKey}
            onCreateApiKey={handleCreateApiKey}
            onRevokeApiKey={handleRevokeApiKey}
            onRefreshKeys={() => {
              loadManagedKeys();
              loadTeamMembers();
            }}
            managementLoading={managementLoading}
            managementError={managementError}
            managementMessage={managementMessage}
            apiKey={apiKey}
          />
        );
      case "Audit Logs":
        return <AuditLogsPage auditLogs={auditLogs} apiKey={apiKey} />;
      case "AI Assistant":
        return (
          <AIAssistantPage
            messages={messages}
            setMessages={setMessages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            apiKey={apiKey}
          />
        );
      default:
        return (
          <OverviewPage
            servers={servers}
            tools={tools}
            auditLogs={auditLogs}
            upstreamHealth={upstreamHealth}
            apiKey={apiKey}
            setActivePage={setActivePage}
          />
        );
    }
  }

  return (
    <AppLayout
      activePage={activePage}
      setActivePage={setActivePage}
      servers={servers}
      connected={Boolean(apiKey)}
      mobileMenuOpen={mobileMenuOpen}
      setMobileMenuOpen={setMobileMenuOpen}
      gatewayProps={{
        apiKey,
        keyInput,
        setKeyInput,
        connectGateway,
        loading,
        connectionStatus,
        apiError,
        onDisconnect: handleDisconnect,
      }}
    >
      {renderCurrentPage()}
    </AppLayout>
  );
}

export default App;
