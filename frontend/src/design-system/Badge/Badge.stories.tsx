import type { Meta, StoryObj } from "@storybook/react";
import { Badge } from "./Badge";

const meta = {
  title: "Design System/Badge",
  component: Badge,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  argTypes: {
    variant: {
      control: "select",
      options: ["default", "secondary", "destructive", "success", "warning", "outline", "muted"],
    },
  },
} satisfies Meta<typeof Badge>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { children: "New" } };
export const Secondary: Story = { args: { variant: "secondary", children: "Draft" } };
export const Success: Story = { args: { variant: "success", children: "Active" } };
export const Destructive: Story = { args: { variant: "destructive", children: "Overdue" } };
export const Warning: Story = { args: { variant: "warning", children: "Pending" } };
export const Outline: Story = { args: { variant: "outline", children: "Beta" } };
export const Muted: Story = { args: { variant: "muted", children: "Archived" } };

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      {(["default","secondary","success","destructive","warning","outline","muted"] as const).map(
        (v) => <Badge key={v} variant={v}>{v}</Badge>
      )}
    </div>
  ),
};
