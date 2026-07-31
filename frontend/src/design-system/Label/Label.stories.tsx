import type { Meta, StoryObj } from "@storybook/react";
import { Label } from "./Label";

const meta = {
  title: "Design System/Label",
  component: Label,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
} satisfies Meta<typeof Label>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { children: "Email address", htmlFor: "email" } };
export const Required: Story = { args: { children: "Full name", htmlFor: "name", required: true } };
export const SrOnly: Story = { args: { children: "Hidden label", htmlFor: "hidden", srOnly: true } };
