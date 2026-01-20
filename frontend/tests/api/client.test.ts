import { beforeEach, describe, expect, it, vi } from "vitest";

type InterceptorFn = (value: any) => any;

const routerMock = vi.hoisted(() => ({
  currentRoute: { value: { name: "home", fullPath: "/" } as any },
  replace: vi.fn(),
}));

const axiosMock = vi.hoisted(() => {
  const requestHandlers: InterceptorFn[] = [];
  const responseSuccessHandlers: InterceptorFn[] = [];
  const responseErrorHandlers: InterceptorFn[] = [];

  const api = {
    defaults: { baseURL: "/api" },
    interceptors: {
      request: {
        use: (fn: InterceptorFn) => {
          requestHandlers.push(fn);
          return 0;
        },
      },
      response: {
        use: (ok: InterceptorFn, err: InterceptorFn) => {
          responseSuccessHandlers.push(ok);
          responseErrorHandlers.push(err);
          return 0;
        },
      },
    },
    __handlers: {
      requestHandlers,
      responseSuccessHandlers,
      responseErrorHandlers,
    },
  };

  return {
    api,
    create: vi.fn(() => api),
  };
});

vi.mock("axios", () => ({ default: axiosMock, create: axiosMock.create }));

describe("api client", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    localStorage.clear();
    routerMock.currentRoute.value = { name: "home", fullPath: "/" } as any;
    (window as any).__xmemRouter = routerMock;
  });

  it("请求拦截器会在 token 存在时设置 Authorization", async () => {
    localStorage.setItem("token", "t");
    const api = (await import("../../src/api/client")).default as any;

    const handler = api.__handlers.requestHandlers[0];
    const cfg = handler({ headers: {} });
    expect(cfg.headers.Authorization).toBe("Bearer t");
  });

  it("响应拦截器在 401 时会清除 token 并尝试跳转登录", async () => {
    localStorage.setItem("token", "t");
    routerMock.currentRoute.value = { name: "todos", fullPath: "/todos?x=1" } as any;
    const api = (await import("../../src/api/client")).default as any;

    const errHandler = api.__handlers.responseErrorHandlers[0];
    const error = { response: { status: 401 } };
    await expect(errHandler(error)).rejects.toBe(error);
    expect(localStorage.getItem("token")).toBeNull();
    expect(routerMock.replace).toHaveBeenCalledWith({ name: "login", query: { redirect: "/todos?x=1" } });
  });
});

