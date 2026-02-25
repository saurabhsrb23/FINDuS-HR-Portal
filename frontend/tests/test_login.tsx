/**
 * Unit tests for the Login page component.
 *
 * Run: npm test -- tests/test_login.tsx
 */

import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ─── Module mocks ─────────────────────────────────────────────────────────────
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
}));

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

jest.mock("@/lib/api", () => ({
  authAPI: {
    login: jest.fn(),
  },
}));

jest.mock("@/lib/auth", () => ({
  setToken: jest.fn(),
  redirectByRole: jest.fn(),
  clearToken: jest.fn(),
  isAuthenticated: jest.fn(() => false),
  getUserRole: jest.fn(() => null),
}));

// ─── Import after mocks ────────────────────────────────────────────────────────
import LoginPage from "@/app/(auth)/login/page";
import { authAPI } from "@/lib/api";
import { setToken, redirectByRole } from "@/lib/auth";
import { toast } from "sonner";

const mockAuthAPI = authAPI as jest.Mocked<typeof authAPI>;
const mockSetToken = setToken as jest.MockedFunction<typeof setToken>;
const mockRedirectByRole = redirectByRole as jest.MockedFunction<
  typeof redirectByRole
>;

// ─── Helpers ──────────────────────────────────────────────────────────────────
function setup() {
  const user = userEvent.setup();
  const utils = render(<LoginPage />);
  return { user, ...utils };
}

// ─── Tests ────────────────────────────────────────────────────────────────────
describe("LoginPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the login form with email and password fields", () => {
    setup();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /sign in/i })
    ).toBeInTheDocument();
  });

  it("renders Candidate and HR tabs", () => {
    setup();
    expect(screen.getByRole("tab", { name: /candidate/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /hr/i })).toBeInTheDocument();
  });

  it("shows validation errors when submitted with empty fields", async () => {
    const { user } = setup();
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/enter a valid email address/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });
  });

  it("shows validation error for invalid email format", async () => {
    const { user } = setup();
    await user.type(screen.getByLabelText(/email address/i), "notanemail");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/enter a valid email address/i)
      ).toBeInTheDocument();
    });
  });

  it("calls authAPI.login with correct credentials on submit", async () => {
    mockAuthAPI.login.mockResolvedValueOnce({
      data: {
        access_token: "tok_access",
        refresh_token: "tok_refresh",
        token_type: "bearer",
        role: "candidate",
        user_id: "user-123",
      },
    } as never);
    mockSetToken.mockResolvedValueOnce(undefined);

    const { user } = setup();
    await user.type(
      screen.getByLabelText(/email address/i),
      "test@example.com"
    );
    await user.type(screen.getByLabelText(/password/i), "MyPass@1!");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockAuthAPI.login).toHaveBeenCalledWith({
        email: "test@example.com",
        password: "MyPass@1!",
      });
    });
  });

  it("redirects to candidate dashboard when role is 'candidate'", async () => {
    mockAuthAPI.login.mockResolvedValueOnce({
      data: {
        access_token: "tok_access",
        refresh_token: "tok_refresh",
        token_type: "bearer",
        role: "candidate",
        user_id: "user-001",
      },
    } as never);
    mockSetToken.mockResolvedValueOnce(undefined);

    const { user } = setup();
    await user.type(screen.getByLabelText(/email address/i), "c@test.com");
    await user.type(screen.getByLabelText(/password/i), "Pass@1234!");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockRedirectByRole).toHaveBeenCalledWith(
        "candidate",
        expect.any(Object)
      );
    });
  });

  it("redirects to recruiter dashboard when role is 'hr'", async () => {
    mockAuthAPI.login.mockResolvedValueOnce({
      data: {
        access_token: "tok_access",
        refresh_token: "tok_refresh",
        token_type: "bearer",
        role: "hr",
        user_id: "user-002",
      },
    } as never);
    mockSetToken.mockResolvedValueOnce(undefined);

    const { user } = setup();
    await user.type(screen.getByLabelText(/email address/i), "hr@test.com");
    await user.type(screen.getByLabelText(/password/i), "Hr@1234!!");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockRedirectByRole).toHaveBeenCalledWith("hr", expect.any(Object));
    });
  });

  it("shows error toast and inline message on wrong credentials (401)", async () => {
    mockAuthAPI.login.mockRejectedValueOnce({
      response: { status: 401, data: { detail: "Invalid email or password" } },
    });

    const { user } = setup();
    await user.type(screen.getByLabelText(/email address/i), "x@test.com");
    await user.type(screen.getByLabelText(/password/i), "WrongPass@1!");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Login failed");
      expect(
        screen.getByText(/invalid email or password/i)
      ).toBeInTheDocument();
    });
  });

  it("shows 403 error for unverified account", async () => {
    mockAuthAPI.login.mockRejectedValueOnce({
      response: {
        status: 403,
        data: { detail: "Email address not verified. Please check your inbox." },
      },
    });

    const { user } = setup();
    await user.type(screen.getByLabelText(/email address/i), "unv@test.com");
    await user.type(screen.getByLabelText(/password/i), "Pass@1234!");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/not verified/i)).toBeInTheDocument();
    });
  });

  it("contains a link to the registration page", () => {
    setup();
    const link = screen.getByRole("link", { name: /create one/i });
    expect(link).toHaveAttribute("href", "/register");
  });

  it("contains a forgot password link", () => {
    setup();
    const link = screen.getByRole("link", { name: /forgot password/i });
    expect(link).toHaveAttribute("href", "/forgot-password");
  });
});
