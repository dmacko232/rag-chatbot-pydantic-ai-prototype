import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Sidebar from "@/components/Sidebar";

const mockSessions = [
  { id: 1, title: "First chat", created_at: "2024-06-01T10:00:00Z" },
  { id: 2, title: "Second chat", created_at: "2024-06-02T10:00:00Z" },
];

describe("Sidebar", () => {
  it("renders all sessions", () => {
    render(
      <Sidebar
        sessions={mockSessions}
        activeSessionId={null}
        onSelectSession={jest.fn()}
        onNewChat={jest.fn()}
        onLogout={jest.fn()}
      />
    );

    expect(screen.getByText("First chat")).toBeInTheDocument();
    expect(screen.getByText("Second chat")).toBeInTheDocument();
  });

  it("calls onSelectSession when clicking a session", async () => {
    const onSelect = jest.fn();
    const user = userEvent.setup();
    render(
      <Sidebar
        sessions={mockSessions}
        activeSessionId={null}
        onSelectSession={onSelect}
        onNewChat={jest.fn()}
        onLogout={jest.fn()}
      />
    );

    await user.click(screen.getByText("First chat"));
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it("calls onNewChat when clicking new chat button", async () => {
    const onNewChat = jest.fn();
    const user = userEvent.setup();
    render(
      <Sidebar
        sessions={[]}
        activeSessionId={null}
        onSelectSession={jest.fn()}
        onNewChat={onNewChat}
        onLogout={jest.fn()}
      />
    );

    await user.click(screen.getByText("+ New Chat"));
    expect(onNewChat).toHaveBeenCalled();
  });

  it("calls onLogout when clicking sign out", async () => {
    const onLogout = jest.fn();
    const user = userEvent.setup();
    render(
      <Sidebar
        sessions={[]}
        activeSessionId={null}
        onSelectSession={jest.fn()}
        onNewChat={jest.fn()}
        onLogout={onLogout}
      />
    );

    await user.click(screen.getByText("Sign out"));
    expect(onLogout).toHaveBeenCalled();
  });

  it("renders empty state with no sessions", () => {
    const { container } = render(
      <Sidebar
        sessions={[]}
        activeSessionId={null}
        onSelectSession={jest.fn()}
        onNewChat={jest.fn()}
        onLogout={jest.fn()}
      />
    );

    expect(screen.getByText("+ New Chat")).toBeInTheDocument();
    expect(screen.getByText("Sign out")).toBeInTheDocument();
  });
});
