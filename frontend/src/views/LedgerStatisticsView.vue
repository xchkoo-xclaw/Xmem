<template>
  <div class="min-h-screen bg-bg text-text">
    <header class="w-full max-w-4xl mx-auto px-4 pt-8 pb-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button
          @click="router.back()"
          class="btn ghost flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          返回
        </button>
        <div class="text-xl font-bold">记账统计</div>
      </div>
    </header>

    <main class="w-full max-w-4xl mx-auto px-4 pb-20">
      <div v-if="loading" class="text-center py-12">
        <p class="text-muted">加载中...</p>
      </div>
      <div v-else-if="statistics" class="space-y-6">
        <div class="bg-surface border border-border rounded-3xl shadow-card p-6 md:p-8">
          <h2 class="text-lg font-bold text-text mb-2">月度日历</h2>
          <div class="flex flex-wrap items-center justify-between gap-2 mb-4 text-sm text-muted">
            <span>{{ calendarMonthLabel }}</span>
            <span class="font-semibold text-text">本月支出 ¥{{ statistics.current_month_total.toLocaleString() }}</span>
          </div>
          <div class="grid grid-cols-7 gap-2 text-xs text-muted mb-2">
            <div v-for="weekday in weekdays" :key="weekday" class="text-center">{{ weekday }}</div>
          </div>
          <div class="grid grid-cols-7 gap-2">
            <div
              v-for="cell in calendarCells"
              :key="cell.key"
              class="min-h-[56px] rounded-lg border border-border/60 p-2 text-xs"
              :class="cell.isCurrentMonth ? 'bg-surface2' : 'bg-transparent text-transparent border-transparent'"
            >
              <div class="flex items-center justify-between text-[11px]">
                <span class="font-medium text-text" v-if="cell.isCurrentMonth">{{ cell.day }}</span>
                <span v-else>0</span>
                <span v-if="cell.isCurrentMonth && cell.count" class="text-muted">{{ cell.count }} 笔</span>
              </div>
              <div v-if="cell.isCurrentMonth" class="mt-1 text-[11px] text-text">
                ¥{{ cell.amount.toLocaleString() }}
              </div>
            </div>
          </div>
        </div>

        <div class="bg-surface border border-border rounded-3xl shadow-card p-6 md:p-8">
          <h2 class="text-lg font-bold text-text mb-4">月度 AI 总结</h2>
          <div v-if="statistics.ai_summary" class="prose prose-sm max-w-none">
            <MdPreview v-secure-display :modelValue="statistics.ai_summary" :theme="theme.resolvedTheme" />
          </div>
          <div v-else class="text-sm text-muted">暂无总结</div>
        </div>

        <div class="bg-surface border border-border rounded-3xl shadow-card p-6 md:p-8">
          <h2 class="text-lg font-bold text-text mb-4">月度预算</h2>
          <div class="flex flex-col gap-4">
            <div class="flex flex-wrap items-center gap-3">
              <span class="text-sm text-muted">{{ calendarMonthLabel }}</span>
              <span v-if="budgetAmount !== null" class="text-sm text-text">
                当前预算 ¥{{ budgetAmount.toLocaleString() }}
              </span>
            </div>
            <div class="flex flex-col md:flex-row gap-3">
              <input
                v-model.number="budgetInput"
                type="number"
                min="0"
                class="input flex-1"
                placeholder="输入本月预算金额"
              />
              <button class="btn primary md:w-32" @click="saveBudget" :disabled="isSavingBudget">
                {{ isSavingBudget ? "保存中..." : "保存预算" }}
              </button>
            </div>
            <div v-if="budgetAmount !== null" class="text-sm" :class="budgetRemaining >= 0 ? 'text-green-600' : 'text-red-600'">
              {{ budgetRemaining >= 0 ? "剩余" : "超出" }} ¥{{ Math.abs(budgetRemaining).toLocaleString() }}
            </div>
          </div>
        </div>

        <div class="bg-surface border border-border rounded-3xl shadow-card p-6 md:p-8">
          <h2 class="text-lg font-bold text-text mb-4">支出分类</h2>
          
          <!-- 分类占比饼图 -->
          <div class="mb-6">
            <h3 class="text-sm font-semibold text-muted mb-3">分类占比</h3>
            <div class="h-80">
              <v-chart :option="categoryChartOption" autoresize />
            </div>
            <div v-if="isNarrowScreen" class="mt-4 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-xs text-muted">
              <div
                v-for="(item, index) in statistics.category_stats"
                :key="item.category"
                class="flex items-center gap-2"
              >
                <span class="w-2.5 h-2.5 rounded-full flex-shrink-0" :style="{ backgroundColor: getCategoryColor(index) }"></span>
                <span class="max-w-32 truncate">{{ item.category }}</span>
              </div>
            </div>
          </div>

          <!-- 分类详情列表 -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div 
              v-for="(item, index) in statistics.category_stats"
              :key="item.category"
              class="flex items-center gap-3 p-3 bg-surface2 border border-border rounded-lg"
            >
              <div 
                class="w-4 h-4 rounded-full flex-shrink-0"
                :style="{ backgroundColor: getCategoryColor(index) }"
              ></div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-sm font-medium text-text truncate">{{ item.category }}</span>
                  <span class="text-sm font-semibold text-text ml-2">¥{{ item.amount.toLocaleString() }}</span>
                </div>
                <div class="flex items-center gap-2">
                  <div class="flex-1 h-2 bg-border/50 rounded-full overflow-hidden">
                    <div
                      class="h-full transition-all duration-300"
                      :style="{ 
                        width: `${item.percentage}%`,
                        backgroundColor: getCategoryColor(index)
                      }"
                    ></div>
                  </div>
                  <span class="text-xs text-muted w-12 text-right">{{ item.percentage.toFixed(1) }}%</span>
                </div>
                <div class="text-xs text-muted mt-1">{{ item.count }} 笔</div>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-surface border border-border rounded-3xl shadow-card p-6 md:p-8">
          <h2 class="text-lg font-bold text-text mb-4">年度总结</h2>
          
          <div class="mb-6">
            <h3 class="text-sm font-semibold text-muted mb-3">全年支出趋势</h3>
            <div class="h-64">
              <v-chart :option="yearlyChartOption" autoresize />
            </div>
          </div>
        </div>
      </div>
      <div v-else class="text-center py-12">
        <p class="text-muted text-lg">暂无统计数据</p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { BarChart, PieChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent
} from "echarts/components";
import { MdPreview } from "md-editor-v3";
import "md-editor-v3/lib/style.css";
import { useDataStore } from "../stores/data";
import type { LedgerStatistics } from "../stores/data";
import { useRouter } from "vue-router";
import { useToastStore } from "../stores/toast";
import { useThemeStore } from "../stores/theme";
import VChart from "vue-echarts";

use([
  CanvasRenderer,
  BarChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent
]);

const router = useRouter();
const toast = useToastStore();
const theme = useThemeStore();

const emit = defineEmits<{
  back: [];
}>();

const data = useDataStore();
const statistics = ref<LedgerStatistics | null>(null);
const loading = ref(true);
const windowWidth = ref(typeof window !== "undefined" ? window.innerWidth : 1024);
const isNarrowScreen = computed(() => windowWidth.value < 560);
const budgetInput = ref<number | null>(null);
const budgetAmount = ref<number | null>(null);
const isSavingBudget = ref(false);
const weekdays = ["日", "一", "二", "三", "四", "五", "六"];

const handleResize = () => {
  windowWidth.value = window.innerWidth;
};

// 年度图表配置
const yearlyChartOption = computed(() => {
  if (!statistics.value || !statistics.value.yearly_data.length) {
    return undefined;
  }

  const months = statistics.value.yearly_data.map(item => {
    const [year, month] = item.month.split('-');
    return `${parseInt(month)}月`;
  });
  const amounts = statistics.value.yearly_data.map(item => item.amount);

  return {
    grid: {
      left: '10%',
      right: '10%',
      top: '10%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: {
        fontSize: 11,
        color: 'rgb(var(--c-text-muted))',
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value: number) => `¥${(value / 1000).toFixed(0)}k`,
        fontSize: 12,
        color: 'rgb(var(--c-text-muted))'
      }
    },
    series: [
      {
        type: 'bar',
        data: amounts,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#8B5CF6' },
              { offset: 1, color: '#A78BFA' }
            ]
          },
          borderRadius: [4, 4, 0, 0]
        },
        barWidth: '50%'
      }
    ],
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const param = params[0];
        return `${param.name}<br/>¥${param.value.toLocaleString()}`;
      }
    }
  };
});

// 分类饼图配置
const categoryChartOption = computed(() => {
  if (!statistics.value || !statistics.value.category_stats.length) {
    return undefined;
  }

  const colors = [
    '#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981',
    '#EF4444', '#06B6D4', '#F97316', '#6366F1', '#14B8A6'
  ];

  const data = statistics.value.category_stats.map((item, index) => ({
    value: item.amount,
    name: item.category,
    itemStyle: {
      color: colors[index % colors.length]
    }
  }));

  return {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        return `${params.name}<br/>¥${params.value.toLocaleString()} (${params.percent}%)`;
      }
    },
    legend: {
      show: !isNarrowScreen.value,
      orient: 'vertical',
      left: 'left',
      top: 'middle',
      textStyle: {
        fontSize: 12,
        color: 'rgb(var(--c-text-muted))'
      }
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: isNarrowScreen.value ? ['50%', '50%'] : ['60%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: 'rgb(var(--c-surface))',
          borderWidth: 2
        },
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          }
        },
        data: data
      }
    ]
  };
});

// 获取分类颜色
const getCategoryColor = (index: number) => {
  const colors = [
    '#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981',
    '#EF4444', '#06B6D4', '#F97316', '#6366F1', '#14B8A6'
  ];
  return colors[index % colors.length];
};

/**
 * 格式化月份显示文案。
 */
const formatMonthLabel = (month: string) => {
  const [year, monthValue] = month.split("-");
  return `${year}年${parseInt(monthValue)}月`;
};

const calendarMonthLabel = computed(() => {
  if (!statistics.value) return "";
  return formatMonthLabel(statistics.value.current_month);
});

const calendarCells = computed(() => {
  if (!statistics.value) return [];
  const [yearStr, monthStr] = statistics.value.current_month.split("-");
  const year = Number(yearStr);
  const month = Number(monthStr);
  const firstDay = new Date(year, month - 1, 1).getDay();
  const daysInMonth = new Date(year, month, 0).getDate();
  const dailyMap = new Map(
    statistics.value.daily_data.map(item => [item.date, item])
  );
  const cells: Array<{
    key: string;
    isCurrentMonth: boolean;
    day: number;
    amount: number;
    count: number;
  }> = [];
  for (let i = 0; i < firstDay; i += 1) {
    cells.push({
      key: `empty-${i}`,
      isCurrentMonth: false,
      day: 0,
      amount: 0,
      count: 0,
    });
  }
  for (let day = 1; day <= daysInMonth; day += 1) {
    const date = `${yearStr}-${monthStr}-${String(day).padStart(2, "0")}`;
    const daily = dailyMap.get(date);
    cells.push({
      key: date,
      isCurrentMonth: true,
      day,
      amount: daily?.amount ?? 0,
      count: daily?.count ?? 0,
    });
  }
  return cells;
});

const budgetRemaining = computed(() => {
  if (budgetAmount.value === null || !statistics.value) return 0;
  return budgetAmount.value - statistics.value.current_month_total;
});

/**
 * 同步预算输入框的默认值。
 */
const syncBudgetInput = () => {
  if (!statistics.value) return;
  budgetAmount.value = statistics.value.budget?.amount ?? null;
  budgetInput.value = budgetAmount.value ?? null;
};

/**
 * 保存当前月份预算。
 */
const saveBudget = async () => {
  if (!statistics.value) return;
  if (budgetInput.value === null || Number.isNaN(budgetInput.value)) {
    toast.warning("请输入预算金额");
    return;
  }
  isSavingBudget.value = true;
  try {
    const result = await data.upsertLedgerBudget(
      statistics.value.current_month,
      Number(budgetInput.value)
    );
    budgetAmount.value = result.amount;
    statistics.value = {
      ...statistics.value,
      budget: result,
    };
    toast.success("预算已保存");
  } catch (error: any) {
    toast.error(error.response?.data?.detail || error.message || "保存预算失败");
  } finally {
    isSavingBudget.value = false;
  }
};

/**
 * 加载记账统计数据。
 */
const loadStatistics = async () => {
  loading.value = true;
  try {
    statistics.value = await data.fetchLedgerStatistics();
    syncBudgetInput();
  } catch (error) {
    console.error("获取统计数据失败:", error);
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  if (typeof window !== "undefined") {
    window.addEventListener("resize", handleResize);
    windowWidth.value = window.innerWidth;
  }
  await loadStatistics();
});

onUnmounted(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("resize", handleResize);
  }
});
</script>

<style scoped>
.echarts {
  width: 100%;
  height: 100%;
}

.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}
.btn.ghost {
  @apply bg-surface text-text border border-border hover:border-border/70;
}
</style>

