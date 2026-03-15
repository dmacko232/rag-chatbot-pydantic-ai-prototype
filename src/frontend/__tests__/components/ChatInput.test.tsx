import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatInput from "@/components/ChatInput";

describe("ChatInput", () => {
  it("calls onSend with trimmed text on submit", async () => {
    const onSend = jest.fn();
    const user = userEvent.setup();
    render(<ChatInput onSend={onSend} />);

    const textarea = screen.getByPlaceholderText(/ask about/i);
    await user.type(textarea, "  Hello world  ");
    await user.click(screen.getByRole("button", { name: /send/i }));

    expect(onSend).toHaveBeenCalledWith("Hello world");
  });

  it("clears input after sending", async () => {
    const user = userEvent.setup();
    render(<ChatInput onSend={jest.fn()} />);

    const textarea = screen.getByPlaceholderText(/ask about/i);
    await user.type(textarea, "Test message");
    await user.click(screen.getByRole("button", { name: /send/i }));

    expect(textarea).toHaveValue("");
  });

  it("does not send empty messages", async () => {
    const onSend = jest.fn();
    const user = userEvent.setup();
    render(<ChatInput onSend={onSend} />);

    await user.click(screen.getByRole("button", { name: /send/i }));
    expect(onSend).not.toHaveBeenCalled();
  });

  it("does not send when disabled", async () => {
    const onSend = jest.fn();
    const user = userEvent.setup();
    render(<ChatInput onSend={onSend} disabled={true} />);

    const textarea = screen.getByPlaceholderText(/ask about/i);
    expect(textarea).toBeDisabled();
  });

  it("sends on Enter key (without Shift)", async () => {
    const onSend = jest.fn();
    const user = userEvent.setup();
    render(<ChatInput onSend={onSend} />);

    const textarea = screen.getByPlaceholderText(/ask about/i);
    await user.type(textarea, "Enter test");
    await user.keyboard("{Enter}");

    expect(onSend).toHaveBeenCalledWith("Enter test");
  });

  it("does not send on Shift+Enter", async () => {
    const onSend = jest.fn();
    const user = userEvent.setup();
    render(<ChatInput onSend={onSend} />);

    const textarea = screen.getByPlaceholderText(/ask about/i);
    await user.type(textarea, "Line 1");
    await user.keyboard("{Shift>}{Enter}{/Shift}");

    expect(onSend).not.toHaveBeenCalled();
  });
});
