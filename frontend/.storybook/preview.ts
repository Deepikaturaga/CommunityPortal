import type { Preview } from "@storybook/react";
import "./preview.css";

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: "^on[A-Z].*" },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    a11y: {
      // axe-core config — run on every story
      config: {
        rules: [
          {
            // colour-contrast is flagged informational in Storybook white canvas;
            // enable for full CI runs
            id: "color-contrast",
            enabled: true,
          },
        ],
      },
    },
    backgrounds: {
      default: "light",
      values: [
        { name: "light", value: "#FFFFFF" },
        { name: "muted", value: "#F8FAFC" },
        { name: "dark", value: "#0F172A" },
      ],
    },
  },
  tags: ["autodocs"],
};

export default preview;
