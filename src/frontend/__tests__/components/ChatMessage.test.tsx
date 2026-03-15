import { render, screen } from "@testing-library/react";
import ChatMessage from "@/components/ChatMessage";

jest.mock("react-markdown", () => {
  return function MockMarkdown({ children }: { children: string }) {
    return <div data-testid="markdown">{children}</div>;
  };
});
jest.mock("remark-gfm", () => () => {});

describe("ChatMessage", () => {
  it("renders user message as plain text", () => {
    render(<ChatMessage role="user" content="Hello there" />);
    expect(screen.getByText("Hello there")).toBeInTheDocument();
  });

  it("renders assistant message through markdown", () => {
    render(<ChatMessage role="assistant" content="**bold answer**" />);
    expect(screen.getByTestId("markdown")).toHaveTextContent("**bold answer**");
  });

  it("displays citations when provided", () => {
    const citations = [{ source_file: "0.txt" }, { source_file: "42.txt" }];
    render(
      <ChatMessage role="assistant" content="Answer" citations={citations} />
    );
    expect(screen.getByText(/0\.txt/)).toBeInTheDocument();
    expect(screen.getByText(/42\.txt/)).toBeInTheDocument();
  });

  it("does not render citation section when empty", () => {
    const { container } = render(
      <ChatMessage role="assistant" content="No sources" citations={[]} />
    );
    expect(container.querySelectorAll("[class*='border-t']")).toHaveLength(0);
  });

  it("shows streaming cursor when isStreaming is true", () => {
    const { container } = render(
      <ChatMessage role="assistant" content="Loading" isStreaming={true} />
    );
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("hides streaming cursor when isStreaming is false", () => {
    const { container } = render(
      <ChatMessage role="assistant" content="Done" isStreaming={false} />
    );
    expect(container.querySelector(".animate-pulse")).not.toBeInTheDocument();
  });
});
