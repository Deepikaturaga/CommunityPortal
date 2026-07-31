import type { Meta, StoryObj } from "@storybook/react";
import { Textarea } from "./Textarea";

const meta = {
  title: "Design System/Textarea",
  component: Textarea,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  decorators: [(S) => <div className="w-80"><S /></div>],
} satisfies Meta<typeof Textarea>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { placeholder: "Enter a description…" } };
export const Filled: Story = { args: { defaultValue: "Lorem ipsum dolor sit amet." } };
export const Invalid: Story = { args: { invalid: true, defaultValue: "Too short" } };
export const Disabled: Story = { args: { disabled: true, placeholder: "Read only" } };
export const NoResize: Story = { args: { resize: "none", placeholder: "Cannot resize" } };
