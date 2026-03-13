"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Citation {
  source_file: string;
}

interface Props {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  isStreaming?: boolean;
}

export default function ChatMessage({ role, content, citations, isStreaming }: Props) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-pink-600 text-white"
            : "bg-white shadow-sm border border-gray-200"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{content}</p>
        ) : (
          <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-a:text-pink-600">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
            {isStreaming && (
              <span className="inline-block h-4 w-1 animate-pulse bg-pink-500 ml-0.5" />
            )}
          </div>
        )}

        {citations && citations.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5 border-t border-gray-100 pt-2">
            {citations.map((c, i) => (
              <span
                key={i}
                className="inline-block rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-600"
              >
                📄 {c.source_file}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
