<template>
  <div class="chart-wrapper">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  LineController,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  LineController,
  Title,
  Tooltip,
  Legend,
  Filler
)

const props = defineProps({
  frames: {
    type: Array,
    required: true,
    default: () => [],
  },
})

const chartCanvas = ref(null)
let chartInstance = null

function updateChart() {
  if (!chartCanvas.value) return

  const labels = props.frames.map((frame) => {
    const date = new Date(frame.timestamp)
    return date.toLocaleTimeString()
  })

  const speeds = props.frames.map((frame) => {
    if (frame.speed === null || frame.speed === undefined) return null
    return (frame.speed * 3.6).toFixed(1) // Convert m/s to km/h
  })

  if (chartInstance) {
    chartInstance.data.labels = labels
    chartInstance.data.datasets[0].data = speeds
    chartInstance.update('none')
  } else {
    const ctx = chartCanvas.value.getContext('2d')
    chartInstance = new ChartJS(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Speed (km/h)',
            data: speeds,
            borderColor: '#667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            mode: 'index',
            intersect: false,
          },
        },
        scales: {
          x: {
            display: true,
            grid: {
              display: false,
            },
          },
          y: {
            display: true,
            title: {
              display: true,
              text: 'Speed (km/h)',
            },
            beginAtZero: true,
          },
        },
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false,
        },
      },
    })
  }
}

watch(
  () => props.frames,
  () => {
    updateChart()
  },
  { deep: true }
)

onMounted(() => {
  updateChart()
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
})
</script>

<style scoped>
.chart-wrapper {
  position: relative;
  height: 400px;
  width: 100%;
}
</style>

