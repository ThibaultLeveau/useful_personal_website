import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { expect, userEvent, within } from "storybook/test";

import { Surface } from "@/components/ui/surface";

import styles from "./auth.module.css";
import { ChangePasswordForm } from "./change-password-form";
import { LoginForm } from "./login-form";

const meta = {
  title: "Authentication/Forms",
  parameters: { layout: "fullscreen" },
  decorators: [
    (Story) => (
      <main className={styles.authMain} style={{ minHeight: "100vh" }}>
        <Surface className={styles.authCard}>
          <Story />
        </Surface>
      </main>
    ),
  ],
} satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

export const Login: Story = {
  render: () => <LoginForm onLogin={async () => undefined} />,
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await userEvent.click(canvas.getByRole("button", { name: "Sign in" }));
    await expect(canvas.getByRole("alert")).toHaveFocus();
    await expect(
      canvas.getByRole("link", { name: "Enter your administrator email." }),
    ).toBeVisible();
  },
};

export const ForcedPasswordChange: Story = {
  render: () => (
    <ChangePasswordForm
      forced
      onChangePassword={async () => undefined}
      onLogout={async () => undefined}
    />
  ),
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await userEvent.click(canvas.getByRole("button", { name: "Change password" }));
    await expect(canvas.getByRole("alert")).toHaveFocus();
    await expect(canvas.getByRole("link", { name: "Enter your current password." })).toBeVisible();
  },
};
