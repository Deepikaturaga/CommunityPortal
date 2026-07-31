import type { Meta, StoryObj } from "@storybook/react";
import { EmptyState } from "./EmptyState";

const meta = {
  title: "Design System/EmptyState",
  component: EmptyState,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  decorators: [(S) => <div className="w-[480px] border border-border rounded-lg"><S /></div>],
} satisfies Meta<typeof EmptyState>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: { title: "No results found" },
};

export const WithDescription: Story = {
  args: {
    title: "No items yet",
    description: "Create your first item to get started.",
  },
};

export const WithAction: Story = {
  args: {
    title: "No projects",
    description: "Get started by creating a new project.",
    actionLabel: "Create project",
    onAction: () => alert("Create project"),
  },
};

export const WithBothActions: Story = {
  args: {
    title: "Inbox zero 🎉",
    description: "You've handled everything. Check back later.",
    actionLabel: "Refresh",
    secondaryActionLabel: "Go to archive",
  },
};

export const CustomIcon: Story = {
  args: {
    title: "No files uploaded",
    description: "Drag and drop files here, or click to browse.",
    actionLabel: "Browse files",
    icon: (
      <svg
        aria-hidden="true"
        width="48"
        height="48"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={1.5}
        className="opacity-40"
      >
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </svg>
    ),
  },
};
