import type { Meta, StoryObj } from "@storybook/react";
import { ErrorState } from "./ErrorState";

const meta = {
  title: "Design System/ErrorState",
  component: ErrorState,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  decorators: [(S) => <div className="w-[480px] border border-border rounded-lg"><S /></div>],
} satisfies Meta<typeof ErrorState>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: {} };

export const WithRetry: Story = {
  args: {
    title: "Failed to load data",
    description: "We could not fetch the resource. Check your connection and try again.",
    actionLabel: "Retry",
    onAction: () => alert("Retry"),
  },
};

export const WithCorrelationId: Story = {
  args: {
    title: "Unexpected error",
    description: "Our team has been notified. Please quote the error ID when contacting support.",
    correlationId: "err_01J9ABCDEF",
    actionLabel: "Retry",
    secondaryActionLabel: "Contact support",
  },
};

export const NetworkError: Story = {
  args: {
    title: "Network error",
    description: "No internet connection detected.",
    actionLabel: "Try again",
  },
};
