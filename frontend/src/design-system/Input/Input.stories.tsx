import type { Meta, StoryObj } from "@storybook/react";
import { Input } from "./Input";

const meta = {
  title: "Design System/Input",
  component: Input,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  decorators: [(S) => <div className="w-72"><S /></div>],
} satisfies Meta<typeof Input>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { placeholder: "Enter text…" } };
export const Filled: Story = { args: { defaultValue: "john@example.com", type: "email" } };
export const Invalid: Story = { args: { invalid: true, defaultValue: "bad-email", "aria-describedby": "err-1" } };
export const Disabled: Story = { args: { disabled: true, placeholder: "Disabled" } };
export const WithLeftAddon: Story = {
  args: {
    placeholder: "Search…",
    leftAddon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
      </svg>
    ),
  },
};
export const Password: Story = { args: { type: "password", placeholder: "Password" } };
