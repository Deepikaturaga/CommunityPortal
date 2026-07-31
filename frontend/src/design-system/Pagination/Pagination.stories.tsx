import type { Meta, StoryObj } from "@storybook/react";
import { useState } from "react";
import { Pagination } from "./Pagination";

const meta = {
  title: "Design System/Pagination",
  component: Pagination,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  argTypes: {
    page: { control: { type: "number", min: 1 } },
    totalPages: { control: { type: "number", min: 1 } },
    siblingCount: { control: { type: "number", min: 0, max: 3 } },
    disabled: { control: "boolean" },
  },
} satisfies Meta<typeof Pagination>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: { page: 3, totalPages: 10, onPageChange: () => {} },
};

export const FewPages: Story = {
  args: { page: 1, totalPages: 3, onPageChange: () => {} },
};

export const LastPage: Story = {
  args: { page: 10, totalPages: 10, onPageChange: () => {} },
};

export const Disabled: Story = {
  args: { page: 5, totalPages: 10, onPageChange: () => {}, disabled: true },
};

export const Interactive: Story = {
  render: () => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const [page, setPage] = useState(1);
    return (
      <div className="flex flex-col gap-4 items-center">
        <p className="text-sm text-muted-foreground">Current page: {page}</p>
        <Pagination page={page} totalPages={20} onPageChange={setPage} />
      </div>
    );
  },
};
