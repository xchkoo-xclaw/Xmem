import { defineStore } from "pinia";

export type ToastType = "success" | "error" | "warning" | "info";

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration?: number; // 持续时间（毫秒），0 表示不自动关闭
  actionLabel?: string;
  onClick?: () => void;
}

export const useToastStore = defineStore("toast", {
  state: () => ({
    toasts: [] as Toast[],
  }),

  actions: {
    show(message: string, type: ToastType = "info", duration: number = 3000, actionLabel?: string, onClick?: () => void) {
      const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const toast: Toast = {
        id,
        message,
        type,
        duration: duration > 0 ? duration : undefined,
        actionLabel,
        onClick,
      };

      this.toasts.push(toast);

      // 如果设置了持续时间，自动移除
      if (duration > 0) {
        setTimeout(() => {
          this.remove(id);
        }, duration);
      }

      return id;
    },

    success(message: string, duration: number = 3000, actionLabel?: string, onClick?: () => void) {
      return this.show(message, "success", duration, actionLabel, onClick);
    },

    error(message: string, duration: number = 3000, actionLabel?: string, onClick?: () => void) {
      return this.show(message, "error", duration, actionLabel, onClick);
    },

    warning(message: string, duration: number = 3000, actionLabel?: string, onClick?: () => void) {
      return this.show(message, "warning", duration, actionLabel, onClick);
    },

    info(message: string, duration: number = 3000, actionLabel?: string, onClick?: () => void) {
      return this.show(message, "info", duration, actionLabel, onClick);
    },

    remove(id: string) {
      const index = this.toasts.findIndex((t) => t.id === id);
      if (index > -1) {
        this.toasts.splice(index, 1);
      }
    },

    runAction(id: string) {
      const toast = this.toasts.find(t => t.id === id);
      if (!toast || !toast.onClick) return;
      try {
        toast.onClick();
      } finally {
        this.remove(id);
      }
    },

    clear() {
      this.toasts = [];
    },
  },
});


