import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "./assets/theme.css";
import "./assets/tailwind.css";
import { vSecureDisplay } from "./directives/secureDisplay";
import { useThemeStore } from "./stores/theme";

const app = createApp(App);
/**
 * 捕获未处理的运行时错误，并引导到 500 页面以便用户恢复。
 */
app.config.errorHandler = (err) => {
  const status = (err as any)?.response?.status;
  if (status === 401 || status === 403) {
    localStorage.removeItem("token");
    const current = router.currentRoute.value;
    const isAuthRoute = current.name === "login" || current.name === "register";
    if (!isAuthRoute) {
      router.replace({ name: "login", query: { redirect: current.fullPath } });
    }
    return;
  }

  router.replace({ name: "server-error" });
};

/**
 * 注入 router 实例给 api 客户端使用，避免 api -> router 的循环依赖。
 */
(window as any).__xmemRouter = router;
const pinia = createPinia();
app.use(pinia);
useThemeStore(pinia).init();
app.use(router).directive("secure-display", vSecureDisplay).mount("#app");
