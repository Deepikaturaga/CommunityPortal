import type { Meta, StoryObj } from "@storybook/react";
import { Select } from "./Select";

const meta = {
  title: "Design System/Select",
  component: Select,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  decorators: [(S) => <div className="w-64"><S /></div>],
} satisfies Meta<typeof Select>;

export default meta;
type Story = StoryObj<typeof meta>;

const options = (
  <>
    <option value="admin">Admin</option>
    <option value="editor">Editor</option>
    <option value="viewer">Viewer</option>
  </>
);

export const Default: Story = { args: { children: options, defaultValue: "editor" } };
export const WithPlaceholder: Story = {
  args: { children: options, placeholder: "Choose a role…" },
};
export const Invalid: Story = { args: { children: options, invalid: true } };
export const Disabled: Story = { args: { children: options, disabled: true, defaultValue: "viewer" } };
