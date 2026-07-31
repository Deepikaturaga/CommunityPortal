import type { Meta, StoryObj } from "@storybook/react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "./Card";
import { Button } from "@ds/Button";

const meta = {
  title: "Design System/Card",
  component: Card,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  decorators: [(S) => <div className="w-80"><S /></div>],
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Card>
      <CardHeader>
        <CardTitle>Card title</CardTitle>
        <CardDescription>Optional description text.</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-foreground">Card body content goes here.</p>
      </CardContent>
      <CardFooter>
        <Button size="sm">Action</Button>
        <Button size="sm" variant="secondary">Cancel</Button>
      </CardFooter>
    </Card>
  ),
};

export const Highlighted: Story = {
  render: () => (
    <Card highlighted>
      <CardContent>
        <p className="text-sm">This card is highlighted (e.g. selected).</p>
      </CardContent>
    </Card>
  ),
};

export const Borderless: Story = {
  render: () => (
    <Card borderless className="bg-muted">
      <CardContent>
        <p className="text-sm">No border, muted background.</p>
      </CardContent>
    </Card>
  ),
};
