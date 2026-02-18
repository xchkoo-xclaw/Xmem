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
        <div class="text-xl font-bold">记账统计</div>
      </div>
    </header>

    <main class="w-full max-w-4xl mx-auto px-4 pb-20">
      <div v-if="loading" class="text-center py-12">
        <p class="text-muted">加载中...</p>
      </div>
      <div v-else-if="hasStatistics" class="space-y-6" data-onboarding="statistics-overview">
        <div id="monthly-calendar" class="bg-surface border border-border rounded-3xl shadow-card p-6 md:p-8">
          <h2 class="text-lg font-bold text-text mb-2">月度日历</h2>
          <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div class="flex items-center gap-2 text-sm text-muted">
              <button class="btn ghost px-2 py-1" @click="shiftCalendarMonth(-1, '#monthly-calendar')">上月</button>
              <span>{{ calendarMonthLabel }}</span>
              <button class="btn ghost px-2 py-1" @click="shiftCalendarMonth(1, '#monthly-calendar')">下月</button>
            </div>
            <span class="text-sm font-semibold text-text">当月支出 ¥{{ calendarStats?.current_month_total.toLocaleString() }}</span>
          </div>
          <div class="grid grid-cols-7 gap-2 text-xs text-muted mb-2">
            <div v-for="weekday in weekdays" :key="weekday" class="text-center">{{ weekday }}</div>
          </div>
          <div class="grid grid-cols-7 gap-2">
            <div
              v-for="cell in calendarCells"
              :key="cell.key"
              class="rounded-lg border border-border/60 p-2 text-xs transition-colors"
              :class="[
                cell.isCurrentMonth ? getCalendarAmountClass(cell.amount) : 'bg-transparent text-transparent border-transparent',
                isNarrowScreen ? 'min-h-[72px]' : 'min-h-[56px]'
              ]"
            >
              <div class="flex items-center justify-between text-[11px]">
                <span class="font-medium text-text" v-if="cell.isCurrentMonth">{{ cell.day }}</span>
                <span v-else>0</span>
                <span v-if="cell.isCurrentMonth && cell.count" class="text-muted hidden sm:inline">{{ cell.count }} 笔</span>
              </div>
              <div v-if="cell.isCurrentMonth" class="mt-1 flex flex-col gap-1 text-[11px] text-text">
                <span class="font-medium">{{ formatCalendarAmount(cell.amount) }}</span>
              </div>
            </div>
          </div>
        </div>

        <div id="monthly-trend" class="bg-surface border border-border rounded-3xl shadow-card p-6 md:p-8">
          <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
            <h2 class="text-lg font-bold text-text">{{ monthlyTrendTitle }}</h2>
            <div class="flex items-center gap-2 text-sm text-muted">
              <button class="btn ghost px-2 py-1" @click="shiftMonthlyTrendRange(-1, '#monthly-trend')">上六个月</button>
              <span>{{ monthlyTrendRangeLabel }}</span>
              <button
                v-if="canShiftToNextSixMonths"
                class="btn ghost px-2 py-1"
                @click="shiftMonthlyTrendRange(1, '#monthly-trend')"
              >
                下六个月
              </button>
            </div>
          </div>
          <div class="h-56">
            <v-chart :option="monthlyTrendOption" autoresize />
          </div>
        </div>

        <div
          id="ledger-note"
          class="bg-surface border border-border rounded-3xl shadow-card p-6 md:p-8 relative overflow-hidden group"
          :class="{ 'ai-loading': summaryGenerating }"
        >
          <div class="flex flex-wrap items-start justify-between gap-3 mb-4">
            <div>
              <h2 class="text-lg font-bold text-text">记账笔记 · 月度 AI 总结</h2>
              <p class="text-xs text-muted mt-1">记账笔记与 AI 总结同步更新</p>
            </div>
            <div class="flex flex-wrap items-center gap-2 text-xs">
              <span
                v-if="summaryStats?.ledger_note_id"
                class="px-2 py-1 rounded-full bg-green-50 text-green-600 border border-green-100"
              >
                已生成记账笔记
              </span>
              <span
                v-else
                class="px-2 py-1 rounded-full bg-surface2 text-muted border border-border"
              >
                尚未生成记账笔记
              </span>
            </div>
          </div>
          <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div class="flex items-center gap-2 text-sm text-muted">
              <button class="btn ghost px-2 py-1" @click="shiftSummaryMonth(-1, '#ledger-note')">上月</button>
              <span>{{ summaryMonthLabel }}</span>
              <button class="btn ghost px-2 py-1" @click="shiftSummaryMonth(1, '#ledger-note')">下月</button>
            </div>
            <div class="flex flex-wrap items-center gap-2 text-sm text-muted">
              <button
                v-if="!summaryStats?.ledger_note_id"
                class="btn ghost px-3 py-1.5"
                @click="handleGenerateLedgerNote"
                :disabled="ledgerNoteGenerating"
              >
                {{ ledgerNoteGenerating ? "生成中..." : "生成记账笔记" }}
              </button>
              <button
                v-if="summaryStats?.ledger_note_id"
                class="btn ghost px-3 py-1.5"
                @click="handleLedgerNoteJump"
              >
                查看记账笔记
              </button>
              <button
                class="btn ghost px-3 py-1.5"
                @click="handleGenerateSummary"
                :disabled="summaryGenerating"
              >
                {{
                  summaryGenerating
                    ? "生成中..."
                    : summaryStats?.ai_summary
                      ? "重新生成AI总结"
                      : "生成AI总结"
                }}
              </button>
            </div>
          </div>
          <div v-if="summaryError" class="text-xs text-red-500 mb-3">
            {{ summaryError }}
          </div>
          <div v-if="summaryGenerating" class="space-y-2">
            <div class="ai-skeleton-line w-3/4"></div>
            <div class="ai-skeleton-line w-2/3"></div>
            <div class="ai-skeleton-line w-1/2"></div>
          </div>
          <div
            v-else-if="summaryStats?.ai_summary"
            :class="[
              'prose',
              'prose-sm',
              'max-w-none',
              'summary-preview',
              theme.resolvedTheme === 'dark' ? 'prose-invert' : ''
            ]"
          >
            <MdPreview v-secure-display :modelValue="summaryStats.ai_summary" :theme="theme.resolvedTheme" />
          </div>
          <div v-else class="text-sm text-muted">暂无总结</div>
        </div>

        <div id="monthly-budget" class="bg-surface border border-border rounded-3xl shadow-card p-6 md:p-8">
          <h2 class="text-lg font-bold text-text mb-4">月度预算</h2>
          <div class="flex flex-col gap-4">
            <div class="flex flex-wrap items-center gap-3">
              <span class="text-sm text-muted">{{ budgetMonthLabel }}</span>
              <span v-if="budgetAmount !== null" class="text-sm text-text">
                当前预算 ¥{{ budgetAmount.toLocaleString() }}
              </span>
            </div>
            <div class="flex flex-col md:flex-row gap-3">
              <input
                v-model.number="budgetInput"
                type="number"
                min="0"
                class="budget-input flex-1 min-w-0"
                placeholder="输入本月预算金额"
              />
              <button class="budget-save-btn w-full md:w-32 md:flex-none" @click="saveBudget" :disabled="isSavingBudget">
                {{ isSavingBudget ? "保存中..." : "保存预算" }}
              </button>
            </div>
            <div v-if="budgetAmount !== null" class="text-sm" :class="budgetRemaining >= 0 ? 'text-green-600' : 'text-red-600'">
              {{ budgetRemaining >= 0 ? "剩余" : "超出" }} ¥{{ Math.abs(budgetRemaining).toLocaleString() }}
            </div>
          </div>
        </div>

        <div id="category-stats" class="bg-surface border border-border rounded-3xl shadow-card p-6 md:p-8">
          <h2 class="text-lg font-bold text-text mb-4">支出分类</h2>
          
          <!-- 分类占比饼图 -->
          <div class="mb-6">
            <h3 class="text-sm font-semibold text-muted mb-3">分类占比</h3>
            <div class="h-80">
              <v-chart :option="categoryChartOption" autoresize />
            </div>
            <div v-if="isNarrowScreen" class="mt-4 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-xs text-muted">
              <div
                v-for="(item, index) in categoryStats?.category_stats || []"
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
              v-for="(item, index) in categoryStats?.category_stats || []"
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

        <div id="yearly-summary" class="bg-surface border border-border rounded-3xl shadow-card p-6 md:p-8">
          <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
            <h2 class="text-lg font-bold text-text">年度总结</h2>
            <div class="flex items-center gap-2 text-sm text-muted">
              <button class="btn ghost px-2 py-1" @click="shiftYearlySummary(-1, '#yearly-summary')">上一年</button>
              <span>{{ yearlySummaryLabel }}</span>
              <button class="btn ghost px-2 py-1" @click="shiftYearlySummary(1, '#yearly-summary')">下一年</button>
            </div>
          </div>
          <div class="mb-6">
            <h3 class="text-sm font-semibold text-muted mb-3">全年支出趋势</h3>
            <div class="h-64">
              <v-chart :option="yearlyChartOption" autoresize />
            </div>
          </div>
        </div>

        <div id="yearly-compare" class="bg-surface border border-border rounded-3xl shadow-card p-6 md:p-8">
          <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
            <h2 class="text-lg font-bold text-text">年度支出对比</h2>
            <div class="flex items-center gap-2 text-sm text-muted">
              <button class="btn ghost px-2 py-1" @click="shiftYearlyCompare(-1, '#yearly-compare')">上一年</button>
              <span>{{ yearlyCompareLabel }}</span>
              <button class="btn ghost px-2 py-1" @click="shiftYearlyCompare(1, '#yearly-compare')">下一年</button>
            </div>
          </div>
          <div class="h-56">
            <v-chart :option="yearlyComparisonOption" autoresize />
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
import { BarChart, LineChart, PieChart, RadarChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  RadarComponent
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
  LineChart,
  PieChart,
  RadarChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  RadarComponent
]);

const router = useRouter();
const toast = useToastStore();
const theme = useThemeStore();

const emit = defineEmits<{
  back: [];
}>();

const handleBack = () => {
  if (window.history.length > 1) {
    router.back();
    return;
  }
  router.push({ name: "home" });
};

const data = useDataStore();
const calendarStats = ref<LedgerStatistics | null>(null);
const summaryStats = ref<LedgerStatistics | null>(null);
const monthlyTrendStats = ref<LedgerStatistics | null>(null);
const categoryStats = ref<LedgerStatistics | null>(null);
const yearlySummaryStats = ref<LedgerStatistics | null>(null);
const yearlyCompareStats = ref<LedgerStatistics | null>(null);
const budgetStats = ref<LedgerStatistics | null>(null);
const loading = ref(true);
const windowWidth = ref(typeof window !== "undefined" ? window.innerWidth : 1024);
const isNarrowScreen = computed(() => windowWidth.value < 560);
const budgetInput = ref<number | null>(null);
const budgetAmount = ref<number | null>(null);
const isSavingBudget = ref(false);
const summaryGenerating = ref(false);
const ledgerNoteGenerating = ref(false);
const summaryError = ref("");
const weekdays = ["日", "一", "二", "三", "四", "五", "六"];
const calendarMonth = ref<string>("");
const summaryMonth = ref<string>("");
const monthlyTrendEndMonth = ref<string>("");
const yearlySummaryYear = ref<number>(new Date().getFullYear());
const yearlyCompareYear = ref<number>(new Date().getFullYear());
const latestTrendEndMonth = ref<string>("");

/**
 * 图表坐标轴与图例文字颜色（适配主题）。
 */
const chartAxisLabelColor = computed(() =>
  theme.resolvedTheme === "dark" ? "rgb(236, 237, 241)" : "rgb(107, 114, 128)"
);

const hasStatistics = computed(() => {
  return Boolean(
    calendarStats.value &&
      summaryStats.value &&
      monthlyTrendStats.value &&
      categoryStats.value &&
      yearlySummaryStats.value &&
      yearlyCompareStats.value &&
      budgetStats.value
  );
});

const handleResize = () => {
  windowWidth.value = window.innerWidth;
};

// 年度图表配置
const yearlyChartOption = computed(() => {
  if (!yearlySummaryStats.value || !yearlySummaryStats.value.yearly_data.length) {
    return undefined;
  }

  const months = yearlySummaryStats.value.yearly_data.map(item => {
    const [year, month] = item.month.split('-');
    return `${parseInt(month)}月`;
  });
  const amounts = yearlySummaryStats.value.yearly_data.map(item => item.amount);

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
        color: chartAxisLabelColor.value,
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value: number) => `¥${(value / 1000).toFixed(0)}k`,
        fontSize: 12,
        color: chartAxisLabelColor.value
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

// 月度趋势图表配置
const monthlyTrendOption = computed(() => {
  if (!monthlyTrendStats.value || !monthlyTrendStats.value.monthly_data.length) {
    return undefined;
  }

  const months = monthlyTrendStats.value.monthly_data.map((item) => {
    const [year, month] = item.month.split("-");
    return `${parseInt(month)}月`;
  });
  const amounts = monthlyTrendStats.value.monthly_data.map((item) => item.amount);

  return {
    grid: {
      left: "10%",
      right: "10%",
      top: "12%",
      bottom: "18%"
    },
    xAxis: {
      type: "category",
      data: months,
      axisLabel: {
        fontSize: 11,
        color: chartAxisLabelColor.value
      }
    },
    yAxis: {
      type: "value",
      axisLabel: {
        formatter: (value: number) => `¥${(value / 1000).toFixed(0)}k`,
        fontSize: 12,
        color: chartAxisLabelColor.value
      }
    },
    series: [
      {
        type: "line",
        data: amounts,
        smooth: true,
        symbol: "circle",
        symbolSize: 6,
        lineStyle: {
          width: 3,
          color: "#10B981"
        },
        itemStyle: {
          color: "#10B981"
        },
        areaStyle: {
          color: "rgba(16, 185, 129, 0.2)"
        }
      }
    ],
    tooltip: {
      trigger: "axis",
      formatter: (params: any) => {
        const param = params[0];
        return `${param.name}<br/>¥${param.value.toLocaleString()}`;
      }
    }
  };
});

// 年度对比图表配置
const yearlyComparisonOption = computed(() => {
  if (!yearlyCompareStats.value || !yearlyCompareStats.value.yearly_totals.length) {
    return undefined;
  }

  const years = yearlyCompareStats.value.yearly_totals.map((item) => `${item.year}年`);
  const amounts = yearlyCompareStats.value.yearly_totals.map((item) => item.amount);
  const maxAmount = Math.max(1, ...amounts);
  const radarMax = Math.ceil(maxAmount * 1.1);

  return {
    radar: {
      shape: "circle",
      radius: "68%",
      indicator: years.map((name) => ({
        name,
        max: radarMax
      })),
      axisName: {
        color: chartAxisLabelColor.value,
        fontSize: 11
      },
      splitLine: {
        lineStyle: {
          color: theme.resolvedTheme === "dark" ? "rgba(255,255,255,0.12)" : "rgba(15,23,42,0.08)"
        }
      },
      splitArea: {
        areaStyle: {
          color:
            theme.resolvedTheme === "dark"
              ? ["rgba(255,255,255,0.02)", "rgba(255,255,255,0.05)"]
              : ["rgba(15,23,42,0.02)", "rgba(15,23,42,0.05)"]
        }
      },
      axisLine: {
        lineStyle: {
          color: theme.resolvedTheme === "dark" ? "rgba(255,255,255,0.2)" : "rgba(15,23,42,0.12)"
        }
      }
    },
    series: [
      {
        type: "radar",
        data: [
          {
            value: amounts,
            name: "年度支出"
          }
        ],
        lineStyle: {
          width: 2,
          color: "#3B82F6"
        },
        itemStyle: {
          color: "#3B82F6"
        },
        areaStyle: {
          color: "rgba(59, 130, 246, 0.22)"
        },
        symbol: "circle",
        symbolSize: 6
      }
    ],
    tooltip: {
      trigger: "item",
      formatter: (params: any) => {
        const data = params?.data?.value || [];
        return years
          .map((label, index) => `${label}：¥${(data[index] || 0).toLocaleString()}`)
          .join("<br/>");
      }
    }
  };
});

// 分类饼图配置
const categoryChartOption = computed(() => {
  if (!categoryStats.value || !categoryStats.value.category_stats.length) {
    return undefined;
  }

  const colors = [
    '#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981',
    '#EF4444', '#06B6D4', '#F97316', '#6366F1', '#14B8A6'
  ];

  const data = categoryStats.value.category_stats.map((item, index) => ({
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
        color: chartAxisLabelColor.value
      }
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: isNarrowScreen.value ? ['50%', '50%'] : ['60%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderColor: 'transparent',
          borderWidth: 0
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

/**
 * 格式化年份显示文案。
 */
const formatYearLabel = (year: number) => {
  return `${year}年`;
};

/**
 * 获取可用的月份字符串。
 */
const resolveMonthValue = (month: string | undefined, fallback: string | undefined) => {
  return month || fallback || new Date().toISOString().slice(0, 7);
};

/**
 * 解析月份字符串为年月数值。
 */
const parseMonthValue = (monthValue: string) => {
  const [year, month] = monthValue.split("-");
  return { year: Number(year), month: Number(month) };
};

/**
 * 计算偏移后的月份字符串。
 */
const shiftMonthValue = (monthValue: string, offset: number) => {
  const { year, month } = parseMonthValue(monthValue);
  const total = year * 12 + (month - 1) + offset;
  const nextYear = Math.floor(total / 12);
  const nextMonth = (total % 12) + 1;
  return `${nextYear}-${String(nextMonth).padStart(2, "0")}`;
};

/**
 * 获取近六个月的起止月份。
 */
const resolveSixMonthRange = (endMonth: string) => {
  const startMonth = shiftMonthValue(endMonth, -5);
  return { startMonth, endMonth };
};

const buildMonthlyLedgerNoteMarkdown = (statistics: LedgerStatistics) => {
  const monthLabel = formatMonthLabel(statistics.current_month);
  const monthTotal = statistics.current_month_total || 0;
  const monthCount = statistics.daily_data.reduce((sum, item) => sum + item.count, 0);
  const lines: string[] = [];
  lines.push(`# 记账笔记（${monthLabel}）`);
  lines.push("");
  lines.push(`统计月份：${statistics.current_month}`);
  lines.push("");
  lines.push(`本月总额：¥${monthTotal.toLocaleString()}`);
  lines.push(`本月笔数：${monthCount} 笔`);
  if (statistics.budget) {
    const remaining = statistics.budget.amount - monthTotal;
    const remainingLabel = remaining >= 0 ? "剩余" : "超出";
    lines.push(
      `预算：¥${statistics.budget.amount.toLocaleString()}，${remainingLabel} ¥${Math.abs(remaining).toLocaleString()}`
    );
  }
  const topDays = [...statistics.daily_data].sort((a, b) => b.amount - a.amount).slice(0, 5);
  if (topDays.length) {
    lines.push("");
    lines.push("金额最高的日期：");
    for (const day of topDays) {
      lines.push(`- ${day.date}：¥${day.amount.toLocaleString()}（${day.count} 笔）`);
    }
  }
  return lines.join("\n");
};

const calendarMonthLabel = computed(() => {
  if (!calendarMonth.value) return "";
  return formatMonthLabel(calendarMonth.value);
});

const summaryMonthLabel = computed(() => {
  if (!summaryMonth.value) return "";
  return formatMonthLabel(summaryMonth.value);
});

const budgetMonthLabel = computed(() => {
  if (!budgetStats.value) return "";
  return formatMonthLabel(budgetStats.value.current_month);
});

const yearlySummaryLabel = computed(() => {
  return formatYearLabel(yearlySummaryYear.value);
});

const yearlyCompareLabel = computed(() => {
  return formatYearLabel(yearlyCompareYear.value);
});

const monthlyTrendRangeLabel = computed(() => {
  if (!monthlyTrendEndMonth.value) return "";
  if (latestTrendEndMonth.value && monthlyTrendEndMonth.value === latestTrendEndMonth.value) {
    return "近六个月";
  }
  const { startMonth, endMonth } = resolveSixMonthRange(monthlyTrendEndMonth.value);
  return `${formatMonthLabel(startMonth)}到${formatMonthLabel(endMonth)}`;
});

const monthlyTrendTitle = computed(() => {
  if (!monthlyTrendEndMonth.value) return "";
  if (latestTrendEndMonth.value && monthlyTrendEndMonth.value === latestTrendEndMonth.value) {
    return "近六个月支出趋势";
  }
  const { startMonth, endMonth } = resolveSixMonthRange(monthlyTrendEndMonth.value);
  return `${formatMonthLabel(startMonth)}到${formatMonthLabel(endMonth)}支出趋势`;
});

const canShiftToNextSixMonths = computed(() => {
  if (!latestTrendEndMonth.value || !monthlyTrendEndMonth.value) return false;
  return monthlyTrendEndMonth.value !== latestTrendEndMonth.value;
});

/**
 * 获取日历中单日最高金额。
 */
const calendarMaxAmount = computed(() => {
  if (!calendarStats.value) return 0;
  const amounts = calendarStats.value.daily_data.map(item => item.amount);
  return amounts.length ? Math.max(...amounts) : 0;
});

/**
 * 生成日历金额配色样式。
 */
const getCalendarAmountClass = (amount: number) => {
  if (amount <= 0) return "bg-surface2";
  const maxAmount = calendarMaxAmount.value;
  if (maxAmount <= 0) {
    return "bg-emerald-50/70 text-text dark:bg-emerald-950/35";
  }
  const threshold = maxAmount * 0.5;
  if (amount < threshold) {
    return "bg-emerald-100/80 text-text dark:bg-emerald-900/30";
  }
  return "bg-emerald-200/90 text-text dark:bg-emerald-800/40";
};

/**
 * 格式化移动端金额显示。
 */
const formatShortAmount = (amount: number) => {
  const absolute = Math.abs(amount);
  if (absolute >= 10000) {
    const value = (absolute / 10000).toFixed(1);
    return `${value.replace(/\\.0$/, "")}万`;
  }
  if (absolute >= 1000) {
    const value = (absolute / 1000).toFixed(1);
    return `${value.replace(/\\.0$/, "")}k`;
  }
  return `${Math.round(absolute)}`;
};

/**
 * 格式化日历金额展示。
 */
const formatCalendarAmount = (amount: number) => {
  if (isNarrowScreen.value) {
    return `¥${formatShortAmount(amount)}`;
  }
  return `¥${amount.toLocaleString()}`;
};

const calendarCells = computed(() => {
  if (!calendarStats.value || !calendarMonth.value) return [];
  const [yearStr, monthStr] = calendarMonth.value.split("-");
  const year = Number(yearStr);
  const month = Number(monthStr);
  const firstDay = new Date(year, month - 1, 1).getDay();
  const daysInMonth = new Date(year, month, 0).getDate();
  const dailyMap = new Map(
    calendarStats.value.daily_data.map(item => [item.date, item])
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
  if (budgetAmount.value === null || !budgetStats.value) return 0;
  return budgetAmount.value - budgetStats.value.current_month_total;
});

/**
 * 同步预算输入框的默认值。
 */
const syncBudgetInput = () => {
  if (!budgetStats.value) return;
  budgetAmount.value = budgetStats.value.budget?.amount ?? null;
  budgetInput.value = budgetAmount.value ?? null;
};

/**
 * 保存当前月份预算。
 */
const saveBudget = async () => {
  if (!budgetStats.value) return;
  if (budgetInput.value === null || Number.isNaN(budgetInput.value)) {
    toast.warning("请输入预算金额");
    return;
  }
  isSavingBudget.value = true;
  try {
    const result = await data.upsertLedgerBudget(
      budgetStats.value.current_month,
      Number(budgetInput.value)
    );
    budgetAmount.value = result.amount;
    budgetStats.value = {
      ...budgetStats.value,
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
 * 加载月度日历统计数据。
 */
const loadCalendarStats = async (month?: string) => {
  try {
    const stats = await data.fetchLedgerStatistics({ month });
    calendarStats.value = stats;
    calendarMonth.value = resolveMonthValue(month, stats.current_month);
  } catch (error) {
    console.error("获取月度日历统计失败:", error);
  }
};

/**
 * 加载月度 AI 总结统计数据。
 */
const loadSummaryStats = async (month?: string) => {
  try {
    const stats = await data.fetchLedgerStatistics({ month });
    summaryStats.value = stats;
    summaryMonth.value = resolveMonthValue(month, stats.current_month);
  } catch (error) {
    console.error("获取月度 AI 总结失败:", error);
  }
};

/**
 * 加载月度趋势统计数据。
 */
const loadMonthlyTrendStats = async (endMonth?: string) => {
  try {
    const stats = await data.fetchLedgerStatistics({ month: endMonth });
    monthlyTrendStats.value = stats;
    const resolvedMonth = resolveMonthValue(endMonth, stats.current_month);
    monthlyTrendEndMonth.value = resolvedMonth;
    if (!latestTrendEndMonth.value && !endMonth) {
      latestTrendEndMonth.value = resolvedMonth;
    }
  } catch (error) {
    console.error("获取月度趋势统计失败:", error);
  }
};

/**
 * 加载支出分类统计数据。
 */
const loadCategoryStats = async (month?: string) => {
  try {
    const stats = await data.fetchLedgerStatistics({ month });
    categoryStats.value = stats;
  } catch (error) {
    console.error("获取分类统计失败:", error);
  }
};

/**
 * 加载月度预算统计数据。
 */
const loadBudgetStats = async (month?: string) => {
  try {
    const stats = await data.fetchLedgerStatistics({ month });
    budgetStats.value = stats;
    syncBudgetInput();
  } catch (error) {
    console.error("获取月度预算统计失败:", error);
  }
};

/**
 * 加载年度总结统计数据。
 */
const loadYearlySummaryStats = async (year?: number) => {
  try {
    const stats = await data.fetchLedgerStatistics({ year });
    yearlySummaryStats.value = stats;
    if (year) {
      yearlySummaryYear.value = year;
    } else {
      yearlySummaryYear.value = Number(stats.current_month.split("-")[0]);
    }
  } catch (error) {
    console.error("获取年度总结统计失败:", error);
  }
};

/**
 * 加载年度对比统计数据。
 */
const loadYearlyCompareStats = async (year?: number) => {
  try {
    const stats = await data.fetchLedgerStatistics({ year });
    yearlyCompareStats.value = stats;
    if (year) {
      yearlyCompareYear.value = year;
    } else {
      yearlyCompareYear.value = Number(stats.current_month.split("-")[0]);
    }
  } catch (error) {
    console.error("获取年度对比统计失败:", error);
  }
};

/**
 * 初始化加载全部统计卡片数据。
 */
const loadAllStatistics = async () => {
  loading.value = true;
  try {
    await Promise.all([
      loadCalendarStats(),
      loadSummaryStats(),
      loadMonthlyTrendStats(),
      loadCategoryStats(),
      loadYearlySummaryStats(),
      loadYearlyCompareStats(),
      loadBudgetStats()
    ]);
  } finally {
    loading.value = false;
  }
};

/**
 * 切换显示月份。
 */
const pushToCard = async (hash: string) => {
  const normalized = hash.startsWith("#") ? hash : `#${hash}`;
  await router.replace({ name: "statistics", hash: normalized });
};

/**
 * 切换月度日历显示月份。
 */
const shiftCalendarMonth = async (offset: number, hash: string) => {
  const baseMonth = resolveMonthValue(calendarMonth.value, calendarStats.value?.current_month);
  const nextMonth = shiftMonthValue(baseMonth, offset);
  calendarMonth.value = nextMonth;
  await loadCalendarStats(nextMonth);
  await pushToCard(hash);
};

/**
 * 切换月度 AI 总结显示月份。
 */
const shiftSummaryMonth = async (offset: number, hash: string) => {
  const baseMonth = resolveMonthValue(summaryMonth.value, summaryStats.value?.current_month);
  const nextMonth = shiftMonthValue(baseMonth, offset);
  summaryMonth.value = nextMonth;
  await loadSummaryStats(nextMonth);
  await pushToCard(hash);
};

const resolveSummaryErrorMessage = (error: any) => {
  const errorCode = error?.code;
  const rawMessage = error?.message || "";
  if (errorCode === "ECONNABORTED" || /timeout/i.test(rawMessage)) {
    return "请求超时，请稍后重试";
  }
  const detail = error?.response?.data?.detail;
  const responseData = error?.response?.data;
  const status = error?.response?.status;
  let message = "";
  if (typeof detail === "string" && detail) {
    message = detail;
  } else if (detail !== undefined) {
    message = JSON.stringify(detail);
  } else if (typeof responseData === "string") {
    message = responseData;
  } else if (responseData) {
    message = JSON.stringify(responseData);
  } else {
    message = error?.message || "";
  }
  if (status) {
    return `生成失败(${status}): ${message || "未知错误"}`;
  }
  return message || "AI 总结生成失败";
};

const handleGenerateLedgerNote = async () => {
  const targetMonth = resolveMonthValue(summaryMonth.value, summaryStats.value?.current_month);
  ledgerNoteGenerating.value = true;
  try {
    const stats = await data.fetchLedgerStatistics({ month: targetMonth });
    const markdown = buildMonthlyLedgerNoteMarkdown(stats);
    const aiSummary = summaryStats.value?.ai_summary?.trim();
    await data.addNoteWithMD(markdown, {
      is_ledger_note: true,
      ledger_month: targetMonth,
      ai_summary: aiSummary || undefined,
    });
    await loadSummaryStats(targetMonth);
    toast.success("记账笔记已生成");
  } catch (error: any) {
    console.error("生成记账笔记失败:", error);
    toast.error(error.response?.data?.detail || error.message || "生成记账笔记失败");
  } finally {
    ledgerNoteGenerating.value = false;
  }
};

/**
 * 手动生成当前月份的 AI 总结。
 */
const handleGenerateSummary = async () => {
  const targetMonth = resolveMonthValue(summaryMonth.value, summaryStats.value?.current_month);
  summaryMonth.value = targetMonth;
  summaryGenerating.value = true;
  summaryError.value = "";
  try {
    const result = await data.generateLedgerMonthlySummary(targetMonth);
    const summary = typeof result?.summary === "string" ? result.summary.trim() : "";
    if (!summary) {
      const message = "AI 返回空总结内容";
      summaryError.value = message;
      toast.error(message);
      return;
    }
    if (summaryStats.value) {
      summaryStats.value = {
        ...summaryStats.value,
        current_month: targetMonth,
        ai_summary: summary,
      };
    }
    await loadSummaryStats(targetMonth);
    toast.success("AI 总结已生成");
  } catch (error: any) {
    const message = resolveSummaryErrorMessage(error);
    summaryError.value = message;
    toast.error(message);
  } finally {
    summaryGenerating.value = false;
  }
};

const handleLedgerNoteJump = () => {
  const noteId = summaryStats.value?.ledger_note_id;
  if (!noteId) return;
  router.push({ name: "note-view", params: { noteId } });
};

/**
 * 切换月度趋势范围。
 */
const shiftMonthlyTrendRange = async (offset: number, hash: string) => {
  const baseMonth = resolveMonthValue(monthlyTrendEndMonth.value, monthlyTrendStats.value?.current_month);
  const nextMonth = shiftMonthValue(baseMonth, offset * 6);
  monthlyTrendEndMonth.value = nextMonth;
  await loadMonthlyTrendStats(nextMonth);
  await pushToCard(hash);
};

/**
 * 切换年度总结显示年份。
 */
const shiftYearlySummary = async (offset: number, hash: string) => {
  yearlySummaryYear.value += offset;
  await loadYearlySummaryStats(yearlySummaryYear.value);
  await pushToCard(hash);
};

/**
 * 切换年度对比显示年份。
 */
const shiftYearlyCompare = async (offset: number, hash: string) => {
  yearlyCompareYear.value += offset;
  await loadYearlyCompareStats(yearlyCompareYear.value);
  await pushToCard(hash);
};

onMounted(async () => {
  if (typeof window !== "undefined") {
    window.addEventListener("resize", handleResize);
    windowWidth.value = window.innerWidth;
  }
  await loadAllStatistics();
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

.budget-input {
  @apply w-full rounded-xl border border-border bg-surface px-4 py-3 text-text placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent/30 transition-shadow shadow-sm;
}

.budget-save-btn {
  @apply rounded-xl border border-border bg-surface text-text font-semibold px-4 py-3 transition-all duration-150 hover:border-border/70 hover:bg-surface2 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed;
}

.ai-skeleton-line {
  @apply h-3 rounded-full bg-surface2;
}

.ai-loading {
  border-color: rgb(255, 90, 180);
  box-shadow: 0 0 18px rgba(255, 90, 180, 0.45);
  animation: ai-rgb-pulse 2.4s ease-in-out infinite;
}

.summary-preview :deep(.md-editor-v-5-preview) {
  background-color: rgb(var(--c-surface));
  color: rgb(var(--c-text));
}

.summary-preview :deep(.md-editor-preview-wrapper),
.summary-preview :deep(.md-editor-preview),
.summary-preview :deep(.md-editor-preview .md-editor-v-5-preview),
.summary-preview :deep(.md-editor-v-5),
.summary-preview :deep(.md-editor-v-5-content) {
  background-color: rgb(var(--c-surface));
  color: rgb(var(--c-text));
}

@keyframes ai-rgb-pulse {
  0% {
    border-color: rgb(255, 90, 180);
    box-shadow: 0 0 18px rgba(255, 90, 180, 0.45);
  }
  33% {
    border-color: rgb(90, 170, 255);
    box-shadow: 0 0 18px rgba(90, 170, 255, 0.45);
  }
  66% {
    border-color: rgb(120, 255, 150);
    box-shadow: 0 0 18px rgba(120, 255, 150, 0.45);
  }
  100% {
    border-color: rgb(255, 90, 180);
    box-shadow: 0 0 18px rgba(255, 90, 180, 0.45);
  }
}
</style>

