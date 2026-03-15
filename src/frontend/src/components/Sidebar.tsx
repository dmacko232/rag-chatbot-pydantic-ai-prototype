"use client";

interface Session {
  id: number;
  title: string;
  created_at: string;
}

interface Props {
  sessions: Session[];
  activeSessionId: number | null;
  onSelectSession: (id: number) => void;
  onNewChat: () => void;
  onLogout: () => void;
}

export default function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onLogout,
}: Props) {
  return (
    <div className="flex h-full w-64 flex-col border-r border-gray-200 bg-white">
      <div className="border-b border-gray-200 p-4">
        <button
          onClick={onNewChat}
          className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50"
        >
          + New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {sessions.map((s) => (
          <button
            key={s.id}
            onClick={() => onSelectSession(s.id)}
            className={`mb-1 w-full rounded-lg px-3 py-2 text-left text-sm transition ${
              activeSessionId === s.id
                ? "bg-pink-50 text-pink-700"
                : "text-gray-700 hover:bg-gray-100"
            }`}
          >
            <p className="truncate font-medium">{s.title || "New chat"}</p>
            <p className="text-xs text-gray-400">
              {new Date(s.created_at).toLocaleDateString()}
            </p>
          </button>
        ))}
      </div>

      <div className="border-t border-gray-200 p-4">
        <button
          onClick={onLogout}
          className="w-full rounded-lg px-4 py-2 text-sm text-gray-600 hover:bg-gray-100"
        >
          Sign out
        </button>
      </div>
    </div>
  );
}
