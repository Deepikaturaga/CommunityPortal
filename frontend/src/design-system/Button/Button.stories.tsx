import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "./Button";

const meta = {
  title: "Design System/Button",
  component: Button,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
  },
  argTypes: {
    variant: {
      control: "select",
      options: ["primary", "secondary", "destructive", "ghost", "link", "outline"],
    },
    size: {
      control: "select",
      options: ["xs", "sm", "md", "lg", "xl", "icon"],
    },
    loading: { control: "boolean" },
    disabled: { control: "boolean" },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: { variant: "primary", children: "Primary button" },
};

export const Secondary: Story = {
  args: { variant: "secondary", children: "Secondary button" },
};

export const Destructive: Story = {
  args: { variant: "destructive", children: "Delete item" },
};

export const Ghost: Story = {
  args: { variant: "ghost", children: "Ghost button" },
};

export const Link: Story = {
  args: { variant: "link", children: "Link button" },
};

export const Outline: Story = {
  args: { variant: "outline", children: "Outline button" },
};

export const Loading: Story = {
  args: { variant: "primary", children: "Saving…", loading: true },
};

export const Disabled: Story = {
  args: { variant: "primary", children: "Cannot click", disabled: true },
};

export const Small: Story = {
  args: { variant: "primary", children: "Small", size: "sm" },
};

export const Large: Story = {
  args: { variant: "primary", children: "Large", size: "lg" },
};

export const WithLeftIcon: Story = {
  args: {
    variant: "primary",
    children: "Add item",
    leftIcon: (
      <svg
        aria-hidden="true"
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path d="M12 5v14M5 12h14" strokeLinecap="round" />
      </svg>
    ),
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-3">
      {(
        ["primary", "secondary", "destructive", "ghost", "outline", "link"] as const
      ).map((v) => (
        <Button key={v} variant={v}>
          {v.charAt(0).toUpperCase() + v.slice(1)}
        </Button>
      ))}
    </div>
  ),
};
