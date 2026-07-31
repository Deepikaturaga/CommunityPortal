import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { FormField } from "@ds/FormField";
import { Input } from "@ds/Input";

describe("FormField", () => {
  it("renders label associated with the control", () => {
    render(
      <FormField id="email" label="Email address">
        <Input />
      </FormField>
    );
    const label = screen.getByText(/email address/i);
    expect(label).toHaveAttribute("for", "email");
    expect(screen.getByRole("textbox")).toHaveAttribute("id", "email");
  });

  it("shows required asterisk on label", () => {
    render(
      <FormField id="name" label="Full name" required>
        <Input />
      </FormField>
    );
    expect(screen.getByText("*")).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toHaveAttribute("aria-required", "true");
  });

  it("shows hint text and wires aria-describedby", () => {
    render(
      <FormField id="user" label="Username" hint="3-20 chars">
        <Input />
      </FormField>
    );
    const hint = screen.getByText(/3-20 chars/i);
    expect(hint).toHaveAttribute("id", "user-hint");
    expect(screen.getByRole("textbox")).toHaveAttribute("aria-describedby", "user-hint");
  });

  it("shows error and marks aria-invalid", () => {
    render(
      <FormField id="pwd" label="Password" error="Too short">
        <Input />
      </FormField>
    );
    const error = screen.getByRole("alert");
    expect(error).toHaveTextContent("Too short");
    expect(screen.getByRole("textbox")).toHaveAttribute("aria-invalid", "true");
  });

  it("hides hint when error is present", () => {
    render(
      <FormField id="x" label="Field" hint="Some hint" error="Required">
        <Input />
      </FormField>
    );
    expect(screen.queryByText(/some hint/i)).not.toBeInTheDocument();
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
