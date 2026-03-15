"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import ChatInput from "@/components/ChatInput";
import ChatMessage from "@/components/ChatMessage";
import Sidebar from "@/components/Sidebar";
import {
  fetchSession,
  fetchSessions,
  isAuthenticated,
  logout,
  streamMessage,
} from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Session {
  id: number;
  title: string;
  created_at: string;
}

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    loadSessions();
  }, [router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function loadSessions() {
    try {
      const data = await fetchSessions();
      setSessions(data);
    } catch {
      // token expired
      router.replace("/login");
    }
  }

  async function loadSession(sessionId: number) {
    setActiveSessionId(sessionId);
    try {
      const data = await fetchSession(sessionId);
      setMessages(
        data.messages.map((m: Message) => ({
          role: m.role,
          content: m.content,
        }))
      );
    } catch {
      setMessages([]);
    }
  }

  function handleNewChat() {
    setActiveSessionId(null);
    setMessages([]);
  }

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  const handleSend = useCallback(
    async (message: string) => {
      setMessages((prev) => [...prev, { role: "user", content: message }]);
      setIsLoading(true);
      setIsThinking(true);

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "" },
      ]);

      try {
        let fullText = "";
        let sessionId = activeSessionId;

        for await (const data of streamMessage(message, activeSessionId ?? undefined)) {
          if (data.text) {
            setIsThinking(false);
            fullText += data.text;
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = {
                role: "assistant",
                content: fullText,
              };
              return updated;
            });
          }
          if (data.done && data.session_id) {
            sessionId = data.session_id;
          }
        }

        if (sessionId && sessionId !== activeSessionId) {
          setActiveSessionId(sessionId);
        }
        loadSessions();
      } catch {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: "Sorry, something went wrong. Please try again.",
          };
          return updated;
        });
      } finally {
        setIsLoading(false);
        setIsThinking(false);
      }
    },
    [activeSessionId]
  );

  return (
    <div className="flex h-screen">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={loadSession}
        onNewChat={handleNewChat}
        onLogout={handleLogout}
      />

      <div className="flex flex-1 flex-col">
        <header className="border-b border-gray-200 bg-white px-6 py-3">
          <h1 className="text-lg font-semibold">Telekom Press Release Assistant</h1>
        </header>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {messages.length === 0 && (
            <div className="flex h-full items-center justify-center text-gray-400">
              <div className="text-center">
                <p className="text-xl font-medium">Ask anything about Deutsche Telekom</p>
                <p className="mt-2 text-sm">
                  Try: &quot;What 5G campus networks has Telekom deployed?&quot;
                </p>
              </div>
            </div>
          )}

          <div className="mx-auto max-w-3xl space-y-4">
            {messages.map((msg, i) => (
              <ChatMessage
                key={i}
                role={msg.role}
                content={msg.content}
                isStreaming={
                  i === messages.length - 1 && msg.role === "assistant" && isLoading
                }
              />
            ))}

            {isThinking && (
              <div className="flex justify-start">
                <div className="rounded-2xl border border-gray-200 bg-white px-4 py-3 shadow-sm">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <div className="flex gap-1">
                      <span className="h-2 w-2 animate-bounce rounded-full bg-pink-400 [animation-delay:0ms]" />
                      <span className="h-2 w-2 animate-bounce rounded-full bg-pink-400 [animation-delay:150ms]" />
                      <span className="h-2 w-2 animate-bounce rounded-full bg-pink-400 [animation-delay:300ms]" />
                    </div>
                    Thinking...
                  </div>
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        </div>

        <div className="border-t border-gray-200 bg-white px-6 py-4">
          <div className="mx-auto max-w-3xl">
            <ChatInput onSend={handleSend} disabled={isLoading} />
          </div>
        </div>
      </div>
    </div>
  );
}
