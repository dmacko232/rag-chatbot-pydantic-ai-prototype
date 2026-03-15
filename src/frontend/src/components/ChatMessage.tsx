"use client";

import { useMemo, type ComponentPropsWithoutRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

const SOURCE_RE = /\[Source:\s*([^\]]+)\]/g;

function extractSources(text: string): string[] {
  const sources = new Set<string>();
  for (const m of text.matchAll(SOURCE_RE)) {
    sources.add(m[1].trim());
  }
  return Array.from(sources);
}

function stripSourceTags(text: string): string {
  return text.replaceAll(SOURCE_RE, "").replace(/\n{3,}/g, "\n\n").trim();
}

const mdComponents = {
  h1: (p: ComponentPropsWithoutRef<"h1">) => (
    <h1 className="mt-5 mb-3 text-xl font-bold text-gray-900" {...p} />
  ),
  h2: (p: ComponentPropsWithoutRef<"h2">) => (
    <h2 className="mt-5 mb-2 text-lg font-semibold text-gray-900" {...p} />
  ),
  h3: (p: ComponentPropsWithoutRef<"h3">) => (
    <h3 className="mt-4 mb-2 text-base font-semibold text-gray-900" {...p} />
  ),
  h4: (p: ComponentPropsWithoutRef<"h4">) => (
    <h4 className="mt-3 mb-1 text-sm font-semibold text-gray-900" {...p} />
  ),
  p: (p: ComponentPropsWithoutRef<"p">) => (
    <p className="my-2 text-sm leading-relaxed text-gray-700" {...p} />
  ),
  ul: (p: ComponentPropsWithoutRef<"ul">) => (
    <ul className="my-2 ml-4 list-disc space-y-1 text-sm text-gray-700" {...p} />
  ),
  ol: (p: ComponentPropsWithoutRef<"ol">) => (
    <ol className="my-2 ml-4 list-decimal space-y-1 text-sm text-gray-700" {...p} />
  ),
  li: (p: ComponentPropsWithoutRef<"li">) => (
    <li className="leading-relaxed" {...p} />
  ),
  strong: (p: ComponentPropsWithoutRef<"strong">) => (
    <strong className="font-semibold text-gray-900" {...p} />
  ),
  a: (p: ComponentPropsWithoutRef<"a">) => (
    <a className="text-pink-600 underline hover:text-pink-800" {...p} />
  ),
  blockquote: (p: ComponentPropsWithoutRef<"blockquote">) => (
    <blockquote className="my-2 border-l-4 border-pink-300 pl-4 italic text-gray-600" {...p} />
  ),
  code: ({ className, children, ...rest }: ComponentPropsWithoutRef<"code">) => {
    const isBlock = className?.includes("language-");
    return isBlock ? (
      <code className={`block my-3 overflow-x-auto rounded-lg bg-gray-900 p-4 text-xs text-gray-100 ${className ?? ""}`} {...rest}>
        {children}
      </code>
    ) : (
      <code className="rounded bg-pink-50 px-1.5 py-0.5 text-xs font-medium text-pink-700" {...rest}>
        {children}
      </code>
    );
  },
  pre: (p: ComponentPropsWithoutRef<"pre">) => (
    <pre className="my-3" {...p} />
  ),
  table: (p: ComponentPropsWithoutRef<"table">) => (
    <div className="my-3 overflow-x-auto">
      <table className="min-w-full text-sm border-collapse" {...p} />
    </div>
  ),
  th: (p: ComponentPropsWithoutRef<"th">) => (
    <th className="border border-gray-200 bg-gray-50 px-3 py-1.5 text-left font-semibold text-gray-900" {...p} />
  ),
  td: (p: ComponentPropsWithoutRef<"td">) => (
    <td className="border border-gray-200 px-3 py-1.5 text-gray-700" {...p} />
  ),
  hr: () => <hr className="my-4 border-gray-200" />,
};

export default function ChatMessage({ role, content, isStreaming }: Props) {
  const isUser = role === "user";
  const sources = useMemo(() => (isUser ? [] : extractSources(content)), [content, isUser]);
  const cleanContent = useMemo(() => (isUser ? content : stripSourceTags(content)), [content, isUser]);

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-5 py-4 ${
          isUser
            ? "bg-pink-600 text-white"
            : "bg-white shadow-sm border border-gray-200"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap text-[15px] leading-relaxed">{content}</p>
        ) : (
          <>
            <div className="max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
                {cleanContent}
              </ReactMarkdown>
              {isStreaming && (
                <span className="inline-block h-4 w-1 animate-pulse bg-pink-500 ml-0.5" />
              )}
            </div>

            {sources.length > 0 && (
              <div className="mt-3 border-t border-gray-100 pt-3">
                <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wide text-gray-400">
                  Sources
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {sources.map((src, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1 rounded-md bg-gray-50 border border-gray-200 px-2 py-1 text-xs text-gray-600"
                    >
                      <svg className="h-3 w-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      {src}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
