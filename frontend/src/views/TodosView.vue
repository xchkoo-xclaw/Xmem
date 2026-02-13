<template>
  <div class="min-h-screen bg-bg text-text">
    <header class="w-full max-w-4xl mx-auto px-4 pt-8 pb-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button
          @click="handleBack"
          class="btn ghost flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          返回
        </button>
        <div class="text-xl font-bold">待办事项</div>
      </div>
    </header>

    <main class="w-full max-w-4xl mx-auto px-4 pb-20">
      <div class="bg-surface border border-border rounded-3xl shadow-card p-6 md:p-8">
        <!-- 添加待办输入框 -->
        <TodoInput class="mb-6" />

        <!-- 待办列表 -->
        <TodoList
          :todos="sortedTodos"
          @toggle="handleToggle"
          @update-title="handleUpdateTitle"
          @delete="handleDelete"
          @delete-group="handleDeleteGroup"
          @delete-item="handleDeleteItem"
          @pin="handlePin"
          @add-group-item="handleAddGroupItem"
          @update-item-title="handleUpdateItemTitle"
          @toggle-item="handleToggleItem"
          :show-completed="true"
          :highlight-todo-id="highlightTodoId"
        />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, nextTick, watch } from "vue";
import { useDataStore } from "../stores/data";
import TodoList from "../components/TodoList.vue";
import TodoInput from "../components/TodoInput.vue";
import { useRouter, useRoute } from "vue-router";

const router = useRouter();
const route = useRoute();

const emit = defineEmits<{
  back: [];
}>();

const data = useDataStore();
const highlightTodoId = ref<number | null>(null);
const highlightTimer = ref<number | null>(null);

/**
 * 处理返回操作，优先返回上一页，必要时回到首页。
 */
const handleBack = () => {
  router.back();
  if (window.history.length <= 1) {
    router.push({ name: "home" });
  }
};

// 排序后的待办列表（按置顶优先，然后按创建时间倒序，最新的在上面）
const sortedTodos = computed(() => {
  return [...data.todos].sort((a, b) => {
    // 置顶的在前
    if (a.is_pinned && !b.is_pinned) return -1;
    if (!a.is_pinned && b.is_pinned) return 1;
    // 然后按创建时间倒序
    const timeA = new Date(a.created_at).getTime();
    const timeB = new Date(b.created_at).getTime();
    return timeB - timeA;
  });
});

/** 进入待办页时拉取全部待办（包含已完成的子待办） */
const applyHighlight = async (todoId: number | null) => {
  if (!todoId) return;
  highlightTodoId.value = todoId;
  await nextTick();
  const target = document.querySelector(`[data-todo-id="${todoId}"]`);
  target?.scrollIntoView({ behavior: "smooth", block: "center" });
  if (highlightTimer.value !== null) {
    window.clearTimeout(highlightTimer.value);
    highlightTimer.value = null;
  }
  highlightTimer.value = window.setTimeout(() => {
    highlightTodoId.value = null;
    highlightTimer.value = null;
  }, 2000);
};

onMounted(async () => {
  await data.fetchTodos();
  const raw = route.query.todoId;
  const id = typeof raw === "string" ? Number(raw) : null;
  if (id && !Number.isNaN(id)) {
    await applyHighlight(id);
  }
});

watch(
  () => route.query.todoId,
  async (value) => {
    const id = typeof value === "string" ? Number(value) : null;
    if (id && !Number.isNaN(id)) {
      await applyHighlight(id);
    }
  }
);

const handleToggle = (id: number) => {
  data.toggleTodo(id);
};

const handleUpdateTitle = (id: number, title: string) => {
  data.updateTodo(id, { title });
};

const handleDelete = (id: number) => {
  data.removeTodo(id);
};

const handleDeleteGroup = (id: number) => {
  data.removeTodo(id);
};

const handleDeleteItem = (id: number) => {
  data.removeTodo(id);
};

const handlePin = (id: number) => {
  data.togglePinTodo(id);
};

const handleAddGroupItem = (groupId: number) => {
  data.addTodo("新建待办", groupId);
};

const handleUpdateItemTitle = (id: number, title: string) => {
  data.updateTodo(id, { title });
};

const handleToggleItem = (id: number) => {
  data.toggleTodo(id);
};
</script>

<style scoped>
.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}
.btn.ghost {
  @apply bg-surface text-text border border-border hover:border-border/70;
}
</style>
