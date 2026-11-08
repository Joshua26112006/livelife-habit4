import { redirect } from "next/navigation";

// The coach landing page (served by the Python demo service) links to every other screen.
export default function Home() {
  redirect("/demo-livelife/choices/");
}
