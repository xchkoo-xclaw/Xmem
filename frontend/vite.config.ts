import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

/**
 * 为本地开发创建 /api 反向代理配置，使其与生产环境 Nginx 行为一致（/api 前缀会被剥离）。
 */
const createLocalApiProxy = () => {
  return {
    "/api": {
      target: "http://localhost:8000",
      changeOrigin: true,
      secure: false,
      rewrite: (path: string) => path.replace(/^\/api/, ""),
    },
  };
};

/**
 * 读取前端 package.json 的 version，用于注入到构建产物（展示在页面 footer 等位置）。
 */
const resolveFrontendVersion = () => {
  const here = path.dirname(fileURLToPath(new URL(import.meta.url)));
  const pkgPath = path.join(here, "package.json");
  const pkg = JSON.parse(readFileSync(pkgPath, "utf-8")) as { version?: string };
  const version = (pkg.version || "0.0.0").trim();
  return version.startsWith("v") ? version : `v${version}`;
};

export default defineConfig({
  plugins: [vue()],
  base: process.env.VITE_BASE && process.env.VITE_BASE.trim() ? process.env.VITE_BASE.trim() : "/",
  define: {
    __APP_VERSION__: JSON.stringify(resolveFrontendVersion()),
  },
  build: {
    rollupOptions: {
      output: {
        inlineDynamicImports: false,
      },
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: createLocalApiProxy(),
  },
});
