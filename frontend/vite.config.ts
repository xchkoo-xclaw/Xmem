import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

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

export default defineConfig({
  plugins: [vue()],
  base: "./",
  server: {
    port: 5173,
    host: true,
    proxy: createLocalApiProxy(),
  },
});
