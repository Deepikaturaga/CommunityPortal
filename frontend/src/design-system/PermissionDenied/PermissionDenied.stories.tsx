import type { Meta, StoryObj } from "@storybook/react";
import { PermissionDenied } from "./PermissionDenied";

const meta = {
  title: "Design System/PermissionDenied",
  component: PermissionDenied,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  decorators: [(S) => <div className="w-[480px] border border-border rounded-lg"><S /></div>],
} satisfies Meta<typeof PermissionDenied>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: {} };

export const WithAction: Story = {
  args: {
    title: "Insufficient permissions",
    description: "You need the 'Admin' role to manage users.",
    actionLabel: "Request access",
    onAction: () => alert("Request sent"),
  },
};

export const WithBothActions: Story = {
  args: {
    title: "Members only",
    description: "This area is restricted to team members.",
    actionLabel: "Join team",
    secondaryActionLabel: "Go back",
    onSecondaryAction: () => history.back(),
  },
};

export const CustomTitle: Story = {
  args: {
    title: "Subscription required",
    description: "Upgrade to a Pro plan to access this feature.",
    actionLabel: "Upgrade now",
  },
};
