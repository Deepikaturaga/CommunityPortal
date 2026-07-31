import type { Meta, StoryObj } from "@storybook/react";
import { FormField } from "./FormField";
import { Input } from "@ds/Input";
import { Select } from "@ds/Select";
import { Textarea } from "@ds/Textarea";

const meta = {
  title: "Design System/FormField",
  component: FormField,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  decorators: [(S) => <div className="w-80"><S /></div>],
} satisfies Meta<typeof FormField>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    id: "email",
    label: "Email address",
    children: <Input type="email" placeholder="you@example.com" />,
  },
};

export const WithHint: Story = {
  args: {
    id: "username",
    label: "Username",
    hint: "Must be 3–20 characters, letters and numbers only.",
    children: <Input placeholder="cool_name42" />,
  },
};

export const WithError: Story = {
  args: {
    id: "password",
    label: "Password",
    required: true,
    error: "Password must be at least 8 characters.",
    children: <Input type="password" defaultValue="abc" />,
  },
};

export const WithSelect: Story = {
  args: {
    id: "role",
    label: "Role",
    required: true,
    children: (
      <Select placeholder="Choose a role…">
        <option value="admin">Admin</option>
        <option value="editor">Editor</option>
      </Select>
    ),
  },
};

export const WithTextarea: Story = {
  args: {
    id: "bio",
    label: "Bio",
    hint: "Tell us a bit about yourself.",
    children: <Textarea placeholder="I am…" />,
  },
};

export const FullForm: Story = {
  render: () => (
    <form
      className="flex flex-col gap-4"
      onSubmit={(e) => e.preventDefault()}
      noValidate
    >
      <FormField id="f-email" label="Email" required>
        <Input type="email" placeholder="you@example.com" />
      </FormField>
      <FormField id="f-role" label="Role" required>
        <Select placeholder="Choose…">
          <option value="admin">Admin</option>
          <option value="viewer">Viewer</option>
        </Select>
      </FormField>
      <FormField id="f-bio" label="Bio" hint="Optional.">
        <Textarea placeholder="Say something…" />
      </FormField>
      <FormField id="f-error" label="Bad field" error="This field is required.">
        <Input placeholder="Oops" />
      </FormField>
    </form>
  ),
};
