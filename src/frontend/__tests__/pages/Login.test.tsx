import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LoginPage from "@/app/login/page";

const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock("@/lib/api", () => ({
  login: jest.fn(),
}));

import { login } from "@/lib/api";
const mockLogin = login as jest.MockedFunction<typeof login>;

describe("LoginPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders login form", () => {
    render(<LoginPage />);
    expect(screen.getByPlaceholderText("Username")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("shows test account hint", () => {
    render(<LoginPage />);
    expect(screen.getByText(/test account/i)).toBeInTheDocument();
  });

  it("calls login and redirects on success", async () => {
    mockLogin.mockResolvedValue({ access_token: "tok123" });
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByPlaceholderText("Username"), "test");
    await user.type(screen.getByPlaceholderText("Password"), "test");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith("test", "test");
      expect(mockPush).toHaveBeenCalledWith("/chat");
    });
  });

  it("shows error on login failure", async () => {
    mockLogin.mockRejectedValue(new Error("Invalid credentials"));
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByPlaceholderText("Username"), "bad");
    await user.type(screen.getByPlaceholderText("Password"), "wrong");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid username or password/i)).toBeInTheDocument();
    });
  });

  it("shows loading state while submitting", async () => {
    let resolveLogin: (value: unknown) => void;
    mockLogin.mockImplementation(
      () => new Promise((resolve) => { resolveLogin = resolve; })
    );
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByPlaceholderText("Username"), "test");
    await user.type(screen.getByPlaceholderText("Password"), "test");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(screen.getByText(/signing in/i)).toBeInTheDocument();

    resolveLogin!({ access_token: "tok" });
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalled();
    });
  });

  it("has a link to register page", () => {
    render(<LoginPage />);
    const link = screen.getByRole("link", { name: /register/i });
    expect(link).toHaveAttribute("href", "/register");
  });
});
