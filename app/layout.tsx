import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "LiveLife · Habit 4 demo",
  description: "Demo of the LiveLife Habit 4 (Think Win-Win) lesson.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0 }}>{children}</body>
    </html>
  );
}
