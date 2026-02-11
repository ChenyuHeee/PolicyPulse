import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";

export default defineConfig({
  integrations: [tailwind()],
  output: "static",
  base: process.env.BASE_PATH && process.env.BASE_PATH !== "" ? process.env.BASE_PATH : "/",
});
